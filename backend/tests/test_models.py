"""Unit tests for SQLAlchemy ORM models — JSON helpers, defaults, and field types."""

import json
from datetime import date

from app.models.recipe import Recipe
from app.models.meal_template import MealTemplate
from app.models.meal_plan import MealPlan
from app.models.meal_history import MealHistory
from app.models.leftover import Leftover
from app.models.veg_availability import VegAvailability
from app.models.shopping_list import ShoppingList
from app.models.household import HouseholdProfile

from tests.conftest import make_recipe_orm, make_template_orm, make_household_orm


# ---------------------------------------------------------------------------
# Recipe model
# ---------------------------------------------------------------------------

class TestRecipeModel:
    def test_create_recipe_with_defaults(self, db_session):
        recipe = Recipe(id="simple", name="Simple Recipe")
        db_session.add(recipe)
        db_session.commit()

        assert recipe.id == "simple"
        assert recipe.name == "Simple Recipe"
        assert recipe.protein_tier == "medium"
        assert recipe.cook_familiarity == "needs_instructions"
        assert recipe.is_side_dish is False

    def test_json_cuisine_tags_roundtrip(self, db_session):
        recipe = make_recipe_orm(db_session, id="tags_test", cuisine_tags=["south_indian", "comfort"])
        assert recipe.get_cuisine_tags() == ["south_indian", "comfort"]

        recipe.set_cuisine_tags(["bengali"])
        db_session.commit()
        db_session.refresh(recipe)
        assert recipe.get_cuisine_tags() == ["bengali"]

    def test_json_ingredients_roundtrip(self, db_session):
        ingredients = [
            {"name": "Tomato", "quantity": "2", "category": "vegetable"},
            {"name": "Salt", "quantity": "1 tsp", "category": "pantry"},
        ]
        recipe = make_recipe_orm(db_session, id="ing_test", ingredients=ingredients)
        loaded = recipe.get_ingredients()
        assert len(loaded) == 2
        assert loaded[0]["name"] == "Tomato"

    def test_json_steps_roundtrip(self, db_session):
        steps = [
            {"order": 1, "instruction": "Boil water", "is_critical": False},
            {"order": 2, "instruction": "Add spices", "is_critical": True},
        ]
        recipe = make_recipe_orm(db_session, id="steps_test", steps=steps)
        loaded = recipe.get_steps()
        assert len(loaded) == 2
        assert loaded[1]["is_critical"] is True

    def test_json_links_roundtrip(self, db_session):
        recipe = make_recipe_orm(
            db_session, id="links_test", links=["https://youtube.com/test"]
        )
        assert recipe.get_links() == ["https://youtube.com/test"]
        recipe.set_links([])
        db_session.commit()
        assert recipe.get_links() == []

    def test_json_side_pairings_roundtrip(self, db_session):
        recipe = make_recipe_orm(
            db_session,
            id="pairings_test",
            preferred_side_pairings=["beans_poriyal", "thayir_pachadi"],
        )
        assert recipe.get_preferred_side_pairings() == ["beans_poriyal", "thayir_pachadi"]

    def test_timestamps_set_on_create(self, db_session):
        recipe = make_recipe_orm(db_session, id="ts_test")
        assert recipe.created_at is not None
        assert recipe.updated_at is not None

    def test_repr(self, db_session):
        recipe = make_recipe_orm(db_session, id="repr_test", name="Sambar")
        assert "repr_test" in repr(recipe)
        assert "Sambar" in repr(recipe)


# ---------------------------------------------------------------------------
# MealTemplate model
# ---------------------------------------------------------------------------

class TestMealTemplateModel:
    def test_create_template(self, db_session):
        tmpl = make_template_orm(db_session, id="south_indian", name="South Indian")
        assert tmpl.id == "south_indian"
        assert tmpl.name == "South Indian"

    def test_json_required_components(self, db_session):
        components = [
            {"role": "main_curry", "description": "Main curry or dal"},
            {"role": "side", "description": "Poriyal or pachadi"},
        ]
        tmpl = make_template_orm(
            db_session, id="comp_test", required_components=components
        )
        loaded = tmpl.get_required_components()
        assert len(loaded) == 2
        assert loaded[0]["role"] == "main_curry"

    def test_json_optional_components(self, db_session):
        tmpl = make_template_orm(
            db_session,
            id="opt_test",
            optional_components=[{"role": "dessert", "description": "Optional sweet"}],
        )
        assert len(tmpl.get_optional_components()) == 1

    def test_json_carb_rules(self, db_session):
        tmpl = make_template_orm(
            db_session, id="carb_test", carb_rules={"default": "rice", "shweta": "roti"}
        )
        rules = tmpl.get_carb_rules()
        assert rules["default"] == "rice"
        assert rules["shweta"] == "roti"

    def test_json_roti_rules(self, db_session):
        tmpl = make_template_orm(
            db_session, id="roti_test", roti_rules={"shweta": "always", "aravind": "extra_5"}
        )
        rules = tmpl.get_roti_rules()
        assert rules["aravind"] == "extra_5"

    def test_repr(self, db_session):
        tmpl = make_template_orm(db_session, id="repr_tmpl", name="North Indian")
        assert "repr_tmpl" in repr(tmpl)


# ---------------------------------------------------------------------------
# HouseholdProfile model
# ---------------------------------------------------------------------------

class TestHouseholdModel:
    def test_create_household(self, db_session):
        profile = make_household_orm(db_session, family_name="Demo Household")
        assert profile.id is not None
        assert profile.family_name == "Demo Household"

    def test_json_members(self, db_session):
        members = [
            {"name": "Planner One", "role": "adult"},
            {"name": "Planner Two", "role": "adult"},
            {"name": "Child", "role": "child"},
        ]
        profile = make_household_orm(db_session, members=members)
        assert len(profile.get_members()) == 3
        assert profile.get_members()[0]["name"] == "Planner One"

    def test_json_cook_info(self, db_session):
        profile = make_household_orm(
            db_session, cook_info={"name": "Cook", "languages": ["hindi", "bengali"]}
        )
        info = profile.get_cook_info()
        assert "hindi" in info["languages"]

    def test_json_rules(self, db_session):
        profile = make_household_orm(
            db_session, rules={"roti_daily": True, "eggs_daily": 5}
        )
        rules = profile.get_rules()
        assert rules["roti_daily"] is True
        assert rules["eggs_daily"] == 5

    def test_json_kid_rules(self, db_session):
        profile = make_household_orm(
            db_session, kid_general_rules=["Less spicy", "Set aside dal before mixing"]
        )
        assert len(profile.get_kid_general_rules()) == 2

    def test_json_pantry_staples(self, db_session):
        profile = make_household_orm(
            db_session, pantry_staples=["salt", "oil", "rice", "turmeric"]
        )
        staples = profile.get_pantry_staples()
        assert "turmeric" in staples

    def test_timestamps(self, db_session):
        profile = make_household_orm(db_session)
        assert profile.created_at is not None
        assert profile.updated_at is not None


# ---------------------------------------------------------------------------
# MealPlan model
# ---------------------------------------------------------------------------

class TestMealPlanModel:
    def test_create_meal_plan(self, db_session):
        plan = MealPlan(plan_date=date(2026, 2, 14), status="draft", template_id="south_indian")
        db_session.add(plan)
        db_session.commit()
        assert plan.id is not None
        assert plan.status == "draft"

    def test_json_dishes_roundtrip(self, db_session):
        plan = MealPlan(plan_date=date(2026, 2, 14))
        plan.set_dishes([{"recipe_id": "sambar", "role": "main"}])
        db_session.add(plan)
        db_session.commit()
        assert plan.get_dishes()[0]["recipe_id"] == "sambar"

    def test_json_shopping_list_roundtrip(self, db_session):
        plan = MealPlan(plan_date=date(2026, 2, 14))
        plan.set_shopping_list([{"name": "Beans", "quantity": "250g"}])
        db_session.add(plan)
        db_session.commit()
        assert plan.get_shopping_list()[0]["name"] == "Beans"


# ---------------------------------------------------------------------------
# MealHistory model
# ---------------------------------------------------------------------------

class TestMealHistoryModel:
    def test_create_history(self, db_session):
        history = MealHistory(history_date=date(2026, 2, 13), cuisine="south_indian")
        db_session.add(history)
        db_session.commit()
        assert history.id is not None

    def test_json_dishes_cooked(self, db_session):
        history = MealHistory(history_date=date(2026, 2, 13))
        history.set_dishes_cooked(["sambar", "beans_poriyal"])
        db_session.add(history)
        db_session.commit()
        assert "sambar" in history.get_dishes_cooked()


# ---------------------------------------------------------------------------
# Leftover model
# ---------------------------------------------------------------------------

class TestLeftoverModel:
    def test_create_leftover(self, db_session):
        leftover = Leftover(
            dish_name="Sambar",
            servings_estimate="1_serving",
            date_logged=date(2026, 2, 13),
        )
        db_session.add(leftover)
        db_session.commit()
        assert leftover.status == "active"
        assert leftover.servings_estimate == "1_serving"


# ---------------------------------------------------------------------------
# VegAvailability model
# ---------------------------------------------------------------------------

class TestVegAvailabilityModel:
    def test_create_veg_snapshot(self, db_session):
        snap = VegAvailability(snapshot_date=date(2026, 2, 14))
        snap.set_vegetables(["beans", "potato", "tomato"])
        snap.set_use_soon(["beans"])
        db_session.add(snap)
        db_session.commit()
        assert len(snap.get_vegetables()) == 3
        assert snap.get_use_soon() == ["beans"]


# ---------------------------------------------------------------------------
# ShoppingList model
# ---------------------------------------------------------------------------

class TestShoppingListModel:
    def test_create_shopping_list(self, db_session):
        sl = ShoppingList(list_date=date(2026, 2, 14), meal_plan_id=1)
        sl.set_items([
            {"name": "Beans", "quantity": "250g", "category": "needed", "for_dish": "beans_poriyal"},
        ])
        db_session.add(sl)
        db_session.commit()
        assert len(sl.get_items()) == 1
        assert sl.get_items()[0]["for_dish"] == "beans_poriyal"
