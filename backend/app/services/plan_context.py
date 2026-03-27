"""Shared plan-context loader — used by cook brief and voice routers.

Avoids duplication of plan-dict / recipes-map / leftovers assembly logic.
"""

from sqlalchemy.orm import Session

from app.models.leftover import Leftover
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe


def load_plan_context(plan: MealPlan, db: Session) -> tuple[dict, dict, list]:
    """Load plan dict, recipes map, and leftovers for a meal plan.

    Returns:
        (plan_dict, recipes_map, leftovers_list)
    """
    dishes = plan.get_dishes()
    plan_dict = {
        "plan_date": plan.plan_date.isoformat(),
        "cuisine": plan.cuisine,
        "dishes": dishes,
        "egg_style": plan.egg_style,
        "roti_count": plan.roti_count,
        "include_curd_rice_side": plan.include_curd_rice_side,
        "kid_notes": plan.kid_notes,
    }

    # Load recipe details — include all fields needed by brief + voice services
    recipe_ids = [d.get("recipe_id") for d in dishes if d.get("recipe_id")]
    recipes_map: dict = {}
    if recipe_ids:
        recipe_records = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
        for r in recipe_records:
            recipes_map[r.id] = {
                "name": r.name,
                "cook_familiarity": r.cook_familiarity,
                "critical_notes": r.critical_notes,
                "steps": r.get_steps(),
                "kid_adaptation": r.kid_adaptation,
                "links": r.get_links(),
                "ingredients": r.get_ingredients(),
                "recipe_audio_url": r.recipe_audio_url,
            }

    # Load leftovers for plan date
    leftovers: list[dict] = []
    active_los = (
        db.query(Leftover)
        .filter(Leftover.date_logged == plan.plan_date, Leftover.status == "active")
        .all()
    )
    if not active_los:
        # Also check consumed ones (they were active at checkin time)
        active_los = (
            db.query(Leftover)
            .filter(Leftover.date_logged == plan.plan_date)
            .all()
        )
    for lo in active_los:
        leftovers.append({
            "dish_name": lo.dish_name,
            "servings_estimate": lo.servings_estimate,
        })

    return plan_dict, recipes_map, leftovers
