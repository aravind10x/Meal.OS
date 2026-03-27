"""Seed a public-safe demo state for screenshots and local evaluation.

Creates:
- one approved plan for tomorrow (home, brief, shopping),
- three draft plans for the following day (plans comparison),
- recent meal history,
- and vegetable snapshots for the same dates.

Safe to re-run. This script replaces demo records for the target dates.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models.meal_history import MealHistory
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.veg_availability import VegAvailability
from app.seed.seed_db import seed_all
from app.services.cook_brief import generate_cook_brief


def _upsert_veg_snapshot(
    db,
    snapshot_date: date,
    vegetables: list[str],
    use_soon: list[str],
) -> None:
    record = (
        db.query(VegAvailability)
        .filter(VegAvailability.snapshot_date == snapshot_date)
        .first()
    )
    if not record:
        record = VegAvailability(snapshot_date=snapshot_date)
        db.add(record)

    record.set_vegetables(vegetables)
    record.set_use_soon(use_soon)


def _upsert_history(
    db,
    history_date: date,
    dishes: list[str],
    egg_style: str,
    cuisine: str,
    notes: str = "",
) -> None:
    record = (
        db.query(MealHistory)
        .filter(MealHistory.history_date == history_date)
        .first()
    )
    if not record:
        record = MealHistory(history_date=history_date)
        db.add(record)

    record.set_dishes_cooked(dishes)
    record.egg_style = egg_style
    record.cuisine = cuisine
    record.notes = notes


def _recipe_context(db, recipe_ids: list[str]) -> dict[str, dict]:
    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()
    context: dict[str, dict] = {}
    for recipe in recipes:
        context[recipe.id] = {
            "name": recipe.name,
            "cook_familiarity": recipe.cook_familiarity,
            "critical_notes": recipe.critical_notes,
            "steps": recipe.get_steps(),
            "kid_adaptation": recipe.kid_adaptation,
            "links": recipe.get_links(),
            "ingredients": recipe.get_ingredients(),
            "recipe_audio_url": recipe.recipe_audio_url,
        }
    return context


def _replace_plan(
    db,
    *,
    plan_date: date,
    status: str,
    template_id: str,
    cuisine: str,
    dishes: list[dict],
    egg_style: str,
    include_curd_rice_side: bool,
    roti_count: str,
    kid_notes: str,
    rationale: str,
    shopping_list: list[dict] | None = None,
    cook_brief_text: str = "",
) -> MealPlan:
    existing = (
        db.query(MealPlan)
        .filter(
            MealPlan.plan_date == plan_date,
            MealPlan.status == status,
            MealPlan.template_id == template_id,
        )
        .first()
    )
    if not existing:
        existing = MealPlan(
            plan_date=plan_date,
            status=status,
            template_id=template_id,
        )
        db.add(existing)

    existing.cuisine = cuisine
    existing.egg_style = egg_style
    existing.include_curd_rice_side = include_curd_rice_side
    existing.roti_count = roti_count
    existing.kid_notes = kid_notes
    existing.rationale = rationale
    existing.cook_brief_text = cook_brief_text
    existing.voice_script_text = ""
    existing.voice_audio_url = None
    existing.approved_at = (
        datetime.now(timezone.utc) if status == "approved" else None
    )
    existing.set_dishes(dishes)
    existing.set_shopping_list(shopping_list or [])
    return existing


def seed_demo_state() -> dict[str, str]:
    Base.metadata.create_all(bind=engine)
    seed_all()

    tomorrow = date.today() + timedelta(days=1)
    compare_date = tomorrow + timedelta(days=1)

    db = SessionLocal()
    try:
        _upsert_history(
            db,
            tomorrow - timedelta(days=1),
            ["Avial", "Cabbage Poriyal"],
            "boiled",
            "South Indian",
            "Simple weekday lunch.",
        )
        _upsert_history(
            db,
            tomorrow - timedelta(days=2),
            ["Palak Paneer"],
            "omelette",
            "North Indian",
            "Higher-protein day.",
        )
        _upsert_history(
            db,
            tomorrow - timedelta(days=3),
            ["Dal Khichdi"],
            "scrambled",
            "Comfort",
            "Kept the meal mild for the child.",
        )
        _upsert_history(
            db,
            tomorrow - timedelta(days=4),
            ["Dhokar Dalna"],
            "fried",
            "Bengali",
            "Weekend special.",
        )

        _upsert_veg_snapshot(
            db,
            tomorrow,
            ["Drumstick", "French Beans", "Carrot", "Cucumber", "Spinach"],
            ["Drumstick", "French Beans"],
        )
        _upsert_veg_snapshot(
            db,
            compare_date,
            ["Spinach", "Paneer", "Bottle Gourd", "Carrot", "Cucumber"],
            ["Spinach", "Bottle Gourd"],
        )

        approved_dishes = [
            {"recipe_id": "sambar", "role": "main_curry", "name": "Sambar"},
            {
                "recipe_id": "beans_poriyal",
                "role": "side_dish",
                "name": "Beans Poriyal",
            },
        ]
        approved_plan_dict = {
            "plan_date": tomorrow.isoformat(),
            "cuisine": "South Indian",
            "dishes": approved_dishes,
            "egg_style": "omelette",
            "roti_count": "standard batch",
            "include_curd_rice_side": False,
            "kid_notes": "Set aside dal before adding sambar masala. Keep one egg portion mild for the child.",
        }
        approved_brief = generate_cook_brief(
            approved_plan_dict,
            _recipe_context(db, ["sambar", "beans_poriyal"]),
            leftovers=[],
        )
        approved_plan = _replace_plan(
            db,
            plan_date=tomorrow,
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            dishes=approved_dishes,
            egg_style="omelette",
            include_curd_rice_side=False,
            roti_count="standard batch",
            kid_notes=approved_plan_dict["kid_notes"],
            rationale="Classic South Indian meal that uses the vegetables already in the kitchen and keeps tomorrow morning simple.",
            cook_brief_text=approved_brief,
        )

        _replace_plan(
            db,
            plan_date=compare_date,
            status="draft",
            template_id="south_indian",
            cuisine="South Indian",
            dishes=approved_dishes,
            egg_style="scrambled",
            include_curd_rice_side=False,
            roti_count="standard batch",
            kid_notes="Keep the beans side mild and hold back one ladle of dal before seasoning.",
            rationale="Classic South Indian meal, uses available beans and drumstick.",
            shopping_list=[{"name": "Drumstick", "category": "needed"}],
        )

        _replace_plan(
            db,
            plan_date=compare_date,
            status="draft",
            template_id="north_indian",
            cuisine="North Indian",
            dishes=[
                {
                    "recipe_id": "palak_paneer",
                    "role": "main_curry",
                    "name": "Palak Paneer",
                }
            ],
            egg_style="boiled",
            include_curd_rice_side=True,
            roti_count="standard batch + 5 extra",
            kid_notes="Make one paneer portion with less chili and keep the spinach texture smooth.",
            rationale="High-protein option with paneer and spinach.",
            shopping_list=[
                {"name": "Paneer", "category": "needed"},
                {"name": "Spinach", "category": "needed"},
            ],
        )

        _replace_plan(
            db,
            plan_date=compare_date,
            status="draft",
            template_id="bengali",
            cuisine="Bengali",
            dishes=[
                {
                    "recipe_id": "dhokar_dalna",
                    "role": "main_curry",
                    "name": "Dhokar Dalna",
                }
            ],
            egg_style="fried",
            include_curd_rice_side=False,
            roti_count="standard batch",
            kid_notes="Serve the child a milder gravy portion with soft rice or a small roti.",
            rationale="Comfort Bengali meal with strong variety from the previous two days.",
            shopping_list=[],
        )

        db.commit()
        db.refresh(approved_plan)
        return {
            "approved_plan_id": str(approved_plan.id),
            "home_date": tomorrow.isoformat(),
            "comparison_date": compare_date.isoformat(),
        }
    finally:
        db.close()


if __name__ == "__main__":
    result = seed_demo_state()
    print(f"Demo state ready: {result}")
