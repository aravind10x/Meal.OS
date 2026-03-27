"""Cook Brief Generator — generates structured cook briefs from approved meal plans.

Produces a formatted text brief including:
- Menu overview
- Dish-by-dish instructions (detail based on cook_familiarity)
- Leftover notes
- Kid adaptation notes
- Quantities

Detail levels by cook_familiarity:
- known → Short reminder (dish name + quantities + critical notes only)
- needs_instructions → Full step-by-step
- new → Full steps + YouTube link + "Pre-recorded audio available" note
"""

from datetime import date


def generate_cook_brief(
    plan: dict,
    recipes: dict[str, dict],
    leftovers: list[dict] | None = None,
    household_rules: dict | None = None,
) -> str:
    """Generate a structured cook brief from an approved meal plan.

    Args:
        plan: The approved meal plan dict with dishes, egg_style, etc.
        recipes: Dict of recipe_id -> full recipe data.
        leftovers: Active leftovers (if any).
        household_rules: Household rules for kid notes, etc.

    Returns:
        Formatted cook brief text.
    """
    plan_date = plan.get("plan_date", date.today().isoformat())
    cuisine = plan.get("cuisine", "")
    dishes = plan.get("dishes", [])
    egg_style = plan.get("egg_style", "boiled")
    roti_count = plan.get("roti_count", "standard batch")
    kid_notes = plan.get("kid_notes", "")
    include_curd_rice = plan.get("include_curd_rice_side", False)

    lines = []

    # Header
    lines.append("━" * 40)
    lines.append(f"COOK BRIEF — {plan_date}")
    lines.append("━" * 40)
    lines.append("")

    # Menu overview
    lines.append("📋 TODAY'S MENU")
    for dish in dishes:
        role = dish.get("role", "")
        name = dish.get("name", dish.get("recipe_id", "Unknown"))
        role_label = _role_label(role)
        lines.append(f"• {role_label}: {name}")

    lines.append(f"• Roti: {roti_count}")
    if include_curd_rice:
        lines.append("• Rice: Yes (optional curd rice side)")
    lines.append(f"• Eggs: {egg_style.capitalize()} (5 eggs total)")
    lines.append("• Salad: Carrots + Cucumber")
    lines.append("")

    # Leftover notes
    if leftovers:
        lines.append("⚠️ LEFTOVER NOTE")
        for lo in leftovers:
            name = lo.get("dish_name", "Unknown")
            servings = lo.get("servings_estimate", "some")
            lines.append(f"• {name} ({servings}) — can be reused, no need to make fresh")
        lines.append("")

    # Kid notes
    if kid_notes:
        lines.append("👶 KID NOTE")
        for note in kid_notes.split(". "):
            note = note.strip()
            if note:
                lines.append(f"• {note}")
        lines.append("")

    # Dish-by-dish instructions (detail level based on cook_familiarity)
    for dish in dishes:
        recipe_id = dish.get("recipe_id", "")
        name = dish.get("name", recipe_id)
        recipe = recipes.get(recipe_id, {})

        if not recipe:
            continue

        familiarity = recipe.get("cook_familiarity", "needs_instructions")
        recipe_audio_url = recipe.get("recipe_audio_url")

        if familiarity == "known":
            # --- KNOWN: Short reminder only ---
            lines.append(f"📝 {name.upper()} — (Cook knows this)")

            # Show key quantities
            ingredients = recipe.get("ingredients", [])
            if ingredients:
                qty_items = []
                for ing in ingredients[:6]:
                    ing_name = ing.get("name", "")
                    ing_qty = ing.get("quantity", "")
                    if ing_name and ing_qty:
                        qty_items.append(f"{ing_name}: {ing_qty}")
                    elif ing_name:
                        qty_items.append(ing_name)
                if qty_items:
                    lines.append(f"   📦 Quantities: {', '.join(qty_items)}")

            # Critical notes
            critical = recipe.get("critical_notes", "")
            if critical:
                lines.append(f"   ⚡ {critical}")

        elif familiarity == "needs_instructions":
            # --- NEEDS INSTRUCTIONS: Full step-by-step ---
            lines.append(f"📝 {name.upper()} — Key Steps")

            steps = recipe.get("steps", [])
            for step in steps:
                order = step.get("order", "")
                instruction = step.get("instruction", "")
                is_critical = step.get("is_critical", False)
                prefix = "⚡" if is_critical else f"{order}."
                lines.append(f"   {prefix} {instruction}")

            # Kid adaptation
            kid_adapt = recipe.get("kid_adaptation", "")
            if kid_adapt:
                lines.append(f"   👶 Kid: {kid_adapt}")

        elif familiarity == "new":
            # --- NEW: Full steps + YouTube + pre-recorded audio note ---
            lines.append(f"📝 {name.upper()} — Full Instructions (NEW RECIPE)")

            steps = recipe.get("steps", [])
            for step in steps:
                order = step.get("order", "")
                instruction = step.get("instruction", "")
                is_critical = step.get("is_critical", False)
                prefix = "⚡" if is_critical else f"{order}."
                lines.append(f"   {prefix} {instruction}")

            # Kid adaptation
            kid_adapt = recipe.get("kid_adaptation", "")
            if kid_adapt:
                lines.append(f"   👶 Kid: {kid_adapt}")

            # YouTube link
            links = recipe.get("links", [])
            if links:
                lines.append(f"   🔗 Video: {links[0]}")

            # Pre-recorded audio note
            if recipe_audio_url:
                lines.append(f"   🔊 Pre-recorded audio instructions available")

        lines.append("")

    return "\n".join(lines)


def _role_label(role: str) -> str:
    """Convert a role string to a human-readable label."""
    labels = {
        "main": "Main",
        "main_curry": "Main Curry",
        "curry": "Curry",
        "side": "Side",
        "side_dish": "Side Dish",
        "accompaniment": "Accompaniment",
        "salad": "Salad",
    }
    return labels.get(role, role.replace("_", " ").title())
