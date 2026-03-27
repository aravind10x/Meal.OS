"""Tests for seed data loading — verifies JSON files are valid and seed functions work correctly."""

import json
from pathlib import Path

from app.models.recipe import Recipe
from app.models.meal_template import MealTemplate
from app.models.household import HouseholdProfile
from app.seed.seed_db import seed_recipes, seed_templates, seed_household, load_json


SEED_DIR = Path(__file__).parent.parent / "app" / "seed"


# ---------------------------------------------------------------------------
# JSON file validity
# ---------------------------------------------------------------------------

class TestSeedJsonFiles:
    def test_recipes_json_valid(self):
        data = load_json("recipes.json")
        assert "main_dishes" in data
        assert "side_dishes" in data
        assert len(data["main_dishes"]) > 0
        assert len(data["side_dishes"]) > 0

    def test_each_recipe_has_required_fields(self):
        data = load_json("recipes.json")
        required_fields = {"id", "name", "cuisine_tags", "ingredients", "steps"}
        for category in ["main_dishes", "side_dishes"]:
            for recipe in data[category]:
                missing = required_fields - set(recipe.keys())
                assert not missing, f"Recipe '{recipe.get('id', '?')}' missing: {missing}"

    def test_recipe_ids_are_unique(self):
        data = load_json("recipes.json")
        all_ids = []
        for category in ["main_dishes", "side_dishes"]:
            for recipe in data[category]:
                all_ids.append(recipe["id"])
        assert len(all_ids) == len(set(all_ids)), f"Duplicate recipe IDs found"

    def test_templates_json_valid(self):
        data = load_json("templates.json")
        assert "meal_templates" in data
        assert len(data["meal_templates"]) >= 5  # south_indian, north_indian, indo_chinese, bengali, comfort

    def test_each_template_has_required_fields(self):
        data = load_json("templates.json")
        required = {"id", "name", "required_components"}
        for tmpl in data["meal_templates"]:
            missing = required - set(tmpl.keys())
            assert not missing, f"Template '{tmpl.get('id', '?')}' missing: {missing}"

    def test_vegetables_json_valid(self):
        data = load_json("vegetables.json")
        assert "vegetables" in data
        assert len(data["vegetables"]) > 0

    def test_pantry_staples_json_valid(self):
        data = load_json("pantry_staples.json")
        assert "pantry_staples" in data
        assert len(data["pantry_staples"]) > 0

    def test_household_json_valid(self):
        data = load_json("household.json")
        assert "household_profile" in data
        profile = data["household_profile"]
        assert "family_name" in profile
        assert "members" in profile
        assert "rules" in profile


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

class TestSeedRecipes:
    def test_seed_recipes_loads_all(self, db_session):
        count = seed_recipes(db_session)
        assert count > 0

        # Verify some known recipes exist
        sambar = db_session.query(Recipe).filter(Recipe.id == "sambar").first()
        assert sambar is not None
        assert sambar.name == "Sambar"

    def test_seed_recipes_idempotent(self, db_session):
        """Running seed twice should not create duplicates."""
        first_count = seed_recipes(db_session)
        second_count = seed_recipes(db_session)
        assert second_count == 0

        total = db_session.query(Recipe).count()
        assert total == first_count

    def test_seeded_recipe_has_ingredients(self, db_session):
        seed_recipes(db_session)
        sambar = db_session.query(Recipe).filter(Recipe.id == "sambar").first()
        ingredients = sambar.get_ingredients()
        assert len(ingredients) > 0
        # Every ingredient should have a name
        for ing in ingredients:
            assert "name" in ing

    def test_seeded_recipe_has_steps(self, db_session):
        seed_recipes(db_session)
        sambar = db_session.query(Recipe).filter(Recipe.id == "sambar").first()
        steps = sambar.get_steps()
        assert len(steps) > 0
        for step in steps:
            assert "order" in step
            assert "instruction" in step

    def test_seeded_recipes_have_valid_protein_tiers(self, db_session):
        seed_recipes(db_session)
        recipes = db_session.query(Recipe).all()
        valid_tiers = {"low", "medium", "high"}
        for recipe in recipes:
            assert recipe.protein_tier in valid_tiers, \
                f"Recipe '{recipe.id}' has invalid protein_tier: {recipe.protein_tier}"


class TestSeedTemplates:
    def test_seed_templates_loads_all(self, db_session):
        count = seed_templates(db_session)
        assert count >= 5  # at least the 5 core templates

    def test_seed_templates_idempotent(self, db_session):
        first_count = seed_templates(db_session)
        second_count = seed_templates(db_session)
        assert second_count == 0

        total = db_session.query(MealTemplate).count()
        assert total == first_count

    def test_seeded_template_has_components(self, db_session):
        seed_templates(db_session)
        south = db_session.query(MealTemplate).filter(MealTemplate.id == "south_indian").first()
        assert south is not None
        assert len(south.get_required_components()) > 0


class TestSeedHousehold:
    def test_seed_household_creates_profile(self, db_session):
        created = seed_household(db_session)
        assert created is True

        profile = db_session.query(HouseholdProfile).first()
        assert profile is not None
        assert len(profile.get_members()) > 0

    def test_seed_household_idempotent(self, db_session):
        seed_household(db_session)
        created_again = seed_household(db_session)
        assert created_again is False

        count = db_session.query(HouseholdProfile).count()
        assert count == 1

    def test_seed_household_has_pantry_staples(self, db_session):
        seed_household(db_session)
        profile = db_session.query(HouseholdProfile).first()
        staples = profile.get_pantry_staples()
        assert len(staples) > 0
