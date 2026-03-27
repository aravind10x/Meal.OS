"""Rules Engine — hard constraint validation for AI-proposed meal plans.

Validates each plan against household rules:
- Roti must be included daily
- Eggs must be included with a valid style
- Salad must be included
- No main dish repetition within N days
- Plan must follow template structure (has a main dish)
"""

from dataclasses import dataclass, field

VALID_EGG_STYLES = {"boiled", "omelette", "scrambled", "fried"}
DEFAULT_REPETITION_GAP_DAYS = 3


@dataclass
class ValidationResult:
    """Result of validating a meal plan against household rules."""
    is_valid: bool = True
    violations: list[str] = field(default_factory=list)
    roti_ok: bool = True
    eggs_ok: bool = True
    salad_ok: bool = True
    repetition_ok: bool = True
    template_ok: bool = True


def validate_plan(
    plan: dict,
    meal_history: list[dict],
    repetition_gap_days: int = DEFAULT_REPETITION_GAP_DAYS,
    require_salad_in_dishes: bool = False,
) -> ValidationResult:
    """Validate a candidate meal plan against all household hard constraints.

    Args:
        plan: A meal plan dict with keys: dishes, egg_style, roti_count, etc.
        meal_history: Recent meal history entries (last N days).
                      Each entry: {date, dishes_cooked: [recipe_ids], egg_style, cuisine}
        repetition_gap_days: Minimum days before a main dish can repeat.
        require_salad_in_dishes: If True, require a dish with role "salad" in the dishes list.

    Returns:
        ValidationResult with individual check results and violations.
    """
    result = ValidationResult()

    _check_roti(plan, result)
    _check_eggs(plan, result)
    _check_salad(plan, result, require_salad_in_dishes)
    _check_repetition(plan, meal_history, repetition_gap_days, result)
    _check_template_structure(plan, result)

    result.is_valid = len(result.violations) == 0
    return result


def _check_roti(plan: dict, result: ValidationResult) -> None:
    """Roti/chapati must be included every day."""
    roti_count = plan.get("roti_count", "")
    if not roti_count or roti_count.strip() == "0":
        result.roti_ok = False
        result.violations.append("Roti/chapati must be included in every meal plan.")


def _check_eggs(plan: dict, result: ValidationResult) -> None:
    """Eggs must be present with a valid style (boiled, omelette, scrambled, fried)."""
    egg_style = plan.get("egg_style", "")
    if not egg_style or egg_style not in VALID_EGG_STYLES:
        result.eggs_ok = False
        result.violations.append(
            f"Eggs must be included with a valid style ({', '.join(sorted(VALID_EGG_STYLES))}). "
            f"Got: '{egg_style}'"
        )


def _check_salad(plan: dict, result: ValidationResult, require_in_dishes: bool) -> None:
    """Salad (carrots + cucumber) must be included daily.

    By default, salad is assumed present. If require_in_dishes is True,
    we check for a dish with role "salad" in the plan's dishes list.
    """
    if require_in_dishes:
        dishes = plan.get("dishes", [])
        has_salad = any(d.get("role") == "salad" for d in dishes)
        if not has_salad:
            result.salad_ok = False
            result.violations.append("Salad (carrots + cucumber) must be included in the meal plan.")


def _check_repetition(
    plan: dict,
    meal_history: list[dict],
    gap_days: int,
    result: ValidationResult,
) -> None:
    """Main dishes must not repeat within the last N days."""
    if not meal_history:
        return

    # Extract main dish recipe IDs from the candidate plan
    dishes = plan.get("dishes", [])
    main_recipe_ids = {
        d.get("recipe_id") for d in dishes
        if d.get("role") in ("main", "main_curry", "curry")
        and d.get("recipe_id")
    }

    if not main_recipe_ids:
        return

    # Gather recently cooked dishes from history within the date gap window
    from datetime import date as date_type, timedelta

    today = date_type.today()
    cutoff = today - timedelta(days=gap_days)

    recent_dishes: set[str] = set()
    for entry in meal_history:
        entry_date_str = entry.get("date", "")
        if entry_date_str:
            try:
                entry_date = date_type.fromisoformat(entry_date_str)
            except (ValueError, TypeError):
                continue
            if entry_date < cutoff:
                continue
        cooked = entry.get("dishes_cooked", [])
        recent_dishes.update(cooked)

    # Check for overlaps
    repeated = main_recipe_ids & recent_dishes
    if repeated:
        result.repetition_ok = False
        dish_names = ", ".join(sorted(repeated))
        result.violations.append(
            f"Main dish(es) repeated within last {gap_days} days: {dish_names}. "
            f"Avoid repeating main dishes too soon."
        )


def _check_template_structure(plan: dict, result: ValidationResult) -> None:
    """Plan must have at least one main dish."""
    dishes = plan.get("dishes", [])
    if not dishes:
        result.template_ok = False
        result.violations.append("Plan must include at least one dish.")
        return

    main_roles = {"main", "main_curry", "curry"}
    has_main = any(d.get("role") in main_roles for d in dishes)
    if not has_main:
        result.template_ok = False
        result.violations.append("Plan must include a main dish (role: main/main_curry/curry).")
