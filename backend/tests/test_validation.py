"""Tests for domain validation — ensures Literal/Enum constraints reject bad data."""

from tests.conftest import make_recipe_data


class TestRecipeValidation:
    """Pydantic schema validation for recipe create/update endpoints."""

    def test_create_recipe_invalid_protein_tier_returns_422(self, client):
        payload = make_recipe_data(id="bad_protein", protein_tier="ultra")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_invalid_cook_familiarity_returns_422(self, client):
        payload = make_recipe_data(id="bad_fam", cook_familiarity="expert")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_invalid_cuisine_tag_returns_422(self, client):
        payload = make_recipe_data(id="bad_cuisine", cuisine_tags=["martian_food"])
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_invalid_meal_template_returns_422(self, client):
        payload = make_recipe_data(id="bad_tmpl", meal_template="space_template")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_invalid_ingredient_category_returns_422(self, client):
        payload = make_recipe_data(
            id="bad_ing",
            ingredients=[{"name": "Something", "quantity": "1", "category": "frozen"}],
        )
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_empty_name_returns_422(self, client):
        payload = make_recipe_data(id="empty_name", name="")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_invalid_id_format_returns_422(self, client):
        """Recipe IDs must be lowercase slugs: ^[a-z][a-z0-9_]*$"""
        payload = make_recipe_data(id="Invalid-ID!", name="Bad ID Recipe")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_id_with_uppercase_returns_422(self, client):
        payload = make_recipe_data(id="UpperCase", name="Upper Case Recipe")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_negative_prep_time_returns_422(self, client):
        payload = make_recipe_data(id="neg_time", prep_time_minutes=-5)
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_negative_cook_time_returns_422(self, client):
        payload = make_recipe_data(id="neg_cook", cook_time_minutes=-10)
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_step_order_zero_returns_422(self, client):
        payload = make_recipe_data(
            id="bad_step",
            steps=[{"order": 0, "instruction": "Do something", "is_critical": False}],
        )
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_empty_ingredient_name_returns_422(self, client):
        payload = make_recipe_data(
            id="empty_ing",
            ingredients=[{"name": "", "quantity": "1 cup", "category": "pantry"}],
        )
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_create_recipe_empty_step_instruction_returns_422(self, client):
        payload = make_recipe_data(
            id="empty_step",
            steps=[{"order": 1, "instruction": "", "is_critical": False}],
        )
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 422

    def test_update_recipe_invalid_protein_tier_returns_422(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="upd_val"))
        resp = client.put("/api/recipes/upd_val", json={"protein_tier": "ultra"})
        assert resp.status_code == 422

    def test_update_recipe_invalid_familiarity_returns_422(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="upd_fam"))
        resp = client.put("/api/recipes/upd_fam", json={"cook_familiarity": "expert"})
        assert resp.status_code == 422

    def test_update_recipe_empty_name_returns_422(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="upd_name"))
        resp = client.put("/api/recipes/upd_name", json={"name": ""})
        assert resp.status_code == 422

    # --- Valid edge cases that should succeed ---

    def test_create_recipe_valid_enum_values_succeed(self, client):
        """All valid protein_tier and cook_familiarity values should work."""
        for tier in ["low", "medium", "high"]:
            resp = client.post(
                "/api/recipes",
                json=make_recipe_data(id=f"tier_{tier}", name=f"Tier {tier}", protein_tier=tier),
            )
            assert resp.status_code == 201, f"protein_tier='{tier}' should be valid"

        for fam in ["known", "needs_instructions", "new"]:
            resp = client.post(
                "/api/recipes",
                json=make_recipe_data(id=f"fam_{fam}", name=f"Fam {fam}", cook_familiarity=fam),
            )
            assert resp.status_code == 201, f"cook_familiarity='{fam}' should be valid"

    def test_create_recipe_all_cuisine_tags_valid(self, client):
        """All defined cuisine tags should be accepted."""
        valid_tags = ["south_indian", "north_indian", "indo_chinese", "bengali", "comfort", "international"]
        for i, tag in enumerate(valid_tags):
            resp = client.post(
                "/api/recipes",
                json=make_recipe_data(id=f"cuisine_{i}", name=f"Cuisine {tag}", cuisine_tags=[tag]),
            )
            assert resp.status_code == 201, f"cuisine_tag='{tag}' should be valid"

    def test_create_recipe_empty_meal_template_allowed(self, client):
        """Empty string is valid for meal_template (default)."""
        payload = make_recipe_data(id="no_tmpl", meal_template="")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 201
