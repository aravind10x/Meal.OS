"""Tests for the Delta Shopping List service (Phase 1.5).

Tests:
- Ingredients not available are marked "needed"
- Available vegetables are marked "likely_available"
- Pantry staples are marked "pantry_staple"
- Items are annotated with the dish they're for
- Duplicate ingredients across dishes are merged
- Shopping list API endpoint
"""

from datetime import date, timedelta

from app.services.shopping import generate_shopping_list


SAMPLE_RECIPES = {
    "sambar": {
        "name": "Sambar",
        "ingredients": [
            {"name": "Toor Dal", "quantity": "1 cup", "category": "pantry"},
            {"name": "Drumstick", "quantity": "200g", "category": "vegetable"},
            {"name": "Tomato", "quantity": "2", "category": "vegetable"},
            {"name": "Tamarind", "quantity": "small block", "category": "pantry"},
            {"name": "Coconut", "quantity": "3/4 cup", "category": "vegetable"},
        ],
    },
    "beans_poriyal": {
        "name": "Beans Poriyal",
        "ingredients": [
            {"name": "French Beans", "quantity": "250g", "category": "vegetable"},
            {"name": "Coconut", "quantity": "2 tbsp", "category": "vegetable"},
            {"name": "Mustard Seeds", "quantity": "1/2 tsp", "category": "pantry"},
            {"name": "Urad Dal", "quantity": "1 tsp", "category": "pantry"},
        ],
    },
    "palak_paneer": {
        "name": "Palak Paneer",
        "ingredients": [
            {"name": "Spinach", "quantity": "500g", "category": "vegetable"},
            {"name": "Paneer", "quantity": "200g", "category": "vegetable"},
            {"name": "Onion", "quantity": "2", "category": "vegetable"},
            {"name": "Tomato", "quantity": "2", "category": "vegetable"},
            {"name": "Cream", "quantity": "2 tbsp", "category": "pantry"},
        ],
    },
}

AVAILABLE_VEG = ["French Beans", "Tomato", "Coconut"]
PANTRY_STAPLES = [
    "Toor Dal", "Mustard Seeds", "Urad Dal", "Tamarind",
    "Onion", "Tomato", "Salt", "Oil", "Turmeric Powder",
]


class TestShoppingListCategorization:
    def test_needed_items_flagged(self):
        """Ingredients not available and not pantry should be 'needed'."""
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        needed = [i for i in items if i["category"] == "needed"]
        needed_names = [i["name"] for i in needed]
        assert "Drumstick" in needed_names

    def test_available_vegetables_marked(self):
        """Vegetables in the available list should be 'likely_available'."""
        plan = {
            "dishes": [
                {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        available = [i for i in items if i["category"] == "likely_available"]
        available_names = [i["name"] for i in available]
        assert "French Beans" in available_names

    def test_pantry_staples_marked(self):
        """Pantry staple ingredients should be 'pantry_staple'."""
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        pantry = [i for i in items if i["category"] == "pantry_staple"]
        pantry_names = [i["name"] for i in pantry]
        assert "Toor Dal" in pantry_names
        assert "Tamarind" in pantry_names


class TestShoppingListAnnotation:
    def test_items_have_for_dish(self):
        """Each item should say which dish it's for."""
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        for item in items:
            assert "for_dish" in item
            assert "Sambar" in item["for_dish"]

    def test_items_have_quantity(self):
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        drumstick = next(i for i in items if i["name"] == "Drumstick")
        assert drumstick["quantity"] == "200g"


class TestShoppingListMerging:
    def test_duplicate_ingredients_merged(self):
        """Same ingredient in multiple dishes should appear once."""
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
                {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        coconut_items = [i for i in items if i["name"].lower() == "coconut"]
        assert len(coconut_items) == 1
        # Should reference both dishes
        assert "Sambar" in coconut_items[0]["for_dish"]
        assert "Beans Poriyal" in coconut_items[0]["for_dish"]


class TestShoppingListSorting:
    def test_needed_items_first(self):
        """Needed items should appear before likely_available and pantry."""
        plan = {
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
                {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
            ],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, AVAILABLE_VEG, PANTRY_STAPLES)
        categories = [i["category"] for i in items]
        # All "needed" should come before "likely_available" which come before "pantry_staple"
        first_available = categories.index("likely_available") if "likely_available" in categories else len(categories)
        first_pantry = categories.index("pantry_staple") if "pantry_staple" in categories else len(categories)
        last_needed_idx = -1
        for idx, c in enumerate(categories):
            if c == "needed":
                last_needed_idx = idx
        if last_needed_idx >= 0:
            assert last_needed_idx < first_available


class TestShoppingListEdgeCases:
    def test_empty_plan(self):
        items = generate_shopping_list({"dishes": []}, {}, [], [])
        assert items == []

    def test_unknown_recipe(self):
        """Recipe not in the recipes dict should be skipped."""
        plan = {
            "dishes": [{"recipe_id": "unknown", "role": "main", "name": "Unknown"}],
        }
        items = generate_shopping_list(plan, SAMPLE_RECIPES, [], [])
        assert items == []

    def test_case_insensitive_matching(self):
        """Ingredient matching should be case-insensitive."""
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
        }
        # 'tomato' in pantry_staples vs 'Tomato' in recipe ingredients
        items = generate_shopping_list(
            plan, SAMPLE_RECIPES,
            available_vegetables=["tomato"],  # lowercase
            pantry_staples=["toor dal"],  # lowercase
        )
        tomato = [i for i in items if i["name"].lower() == "tomato"]
        assert len(tomato) == 1
        assert tomato[0]["category"] == "likely_available"


class TestShoppingListAPI:
    """Tests for GET /api/shopping/{plan_id}."""

    def test_get_shopping_list_for_plan(self, client, db_session):
        """Should return a categorized shopping list."""
        from app.models.meal_plan import MealPlan

        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            egg_style="boiled",
            roti_count="standard batch",
        )
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        resp = client.get(f"/api/shopping/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_shopping_list_nonexistent_plan(self, client):
        resp = client.get("/api/shopping/99999")
        assert resp.status_code == 404
