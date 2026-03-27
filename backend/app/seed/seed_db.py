"""Seed the database with initial data from JSON files."""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.recipe import Recipe
from app.models.meal_template import MealTemplate
from app.models.household import HouseholdProfile

SEED_DIR = Path(__file__).parent


def load_json(filename: str) -> dict:
    with open(SEED_DIR / filename, "r") as f:
        return json.load(f)


def seed_recipes(db: Session) -> int:
    """Seed recipes from recipes.json. Returns count of recipes added."""
    data = load_json("recipes.json")
    count = 0

    for category in ["main_dishes", "side_dishes"]:
        for recipe_data in data.get(category, []):
            existing = db.query(Recipe).filter(Recipe.id == recipe_data["id"]).first()
            if existing:
                continue

            recipe = Recipe(
                id=recipe_data["id"],
                name=recipe_data["name"],
                description=recipe_data.get("description", ""),
                cuisine_tags=json.dumps(recipe_data.get("cuisine_tags", [])),
                meal_template=recipe_data.get("meal_template", ""),
                is_side_dish=(category == "side_dishes"),
                ingredients=json.dumps(recipe_data.get("ingredients", [])),
                steps=json.dumps(recipe_data.get("steps", [])),
                critical_notes=recipe_data.get("critical_notes", ""),
                kid_adaptation=recipe_data.get("kid_adaptation", ""),
                preferred_side_pairings=json.dumps(recipe_data.get("preferred_side_pairings", [])),
                protein_tier=recipe_data.get("protein_tier", "medium"),
                cook_familiarity=recipe_data.get("cook_familiarity", "needs_instructions"),
                links=json.dumps(recipe_data.get("links", [])),
                serves=recipe_data.get("serves", "3-4"),
                prep_time_minutes=recipe_data.get("prep_time_minutes"),
                cook_time_minutes=recipe_data.get("cook_time_minutes"),
            )
            db.add(recipe)
            count += 1

    db.commit()
    return count


def seed_templates(db: Session) -> int:
    """Seed meal templates from templates.json. Returns count added."""
    data = load_json("templates.json")
    count = 0

    for tmpl_data in data.get("meal_templates", []):
        existing = db.query(MealTemplate).filter(MealTemplate.id == tmpl_data["id"]).first()
        if existing:
            continue

        tmpl = MealTemplate(
            id=tmpl_data["id"],
            name=tmpl_data["name"],
            description=tmpl_data.get("description", ""),
            required_components=json.dumps(tmpl_data.get("required_components", [])),
            optional_components=json.dumps(tmpl_data.get("optional_components", [])),
            carb_rules=json.dumps(tmpl_data.get("carb_rules", {})),
            roti_rules=json.dumps(tmpl_data.get("roti_rules", {})),
        )
        db.add(tmpl)
        count += 1

    db.commit()
    return count


def seed_household(db: Session) -> bool:
    """Seed household profile from household.json. Returns True if created."""
    existing = db.query(HouseholdProfile).first()
    if existing:
        return False

    data = load_json("household.json")
    profile_data = data["household_profile"]

    # Load pantry staples into a flat list
    pantry_data = load_json("pantry_staples.json")
    pantry_items = []
    for category in pantry_data.get("pantry_staples", []):
        for item in category.get("items", []):
            pantry_items.append(item["name"])

    profile = HouseholdProfile(
        family_name=profile_data.get("family_name", ""),
        members=json.dumps(profile_data.get("members", [])),
        cook_info=json.dumps(profile_data.get("cook", {})),
        rules=json.dumps(profile_data.get("rules", {})),
        kid_general_rules=json.dumps(profile_data.get("kid_general_rules", [])),
        pantry_staples=json.dumps(pantry_items),
    )
    db.add(profile)
    db.commit()
    return True


def seed_all() -> dict:
    """Run all seed functions. Returns summary of what was seeded.

    Safe to call multiple times — skips existing data.
    """
    db = SessionLocal()
    try:
        recipes_count = seed_recipes(db)
        templates_count = seed_templates(db)
        household_created = seed_household(db)

        return {
            "recipes_added": recipes_count,
            "templates_added": templates_count,
            "household_created": household_created,
        }
    finally:
        db.close()


if __name__ == "__main__":
    # When run as CLI command: ensure tables exist, then seed
    Base.metadata.create_all(bind=engine)
    result = seed_all()
    print(f"Seed complete: {result}")
