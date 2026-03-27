"""API integration tests for Recipe CRUD endpoints."""

from tests.conftest import make_recipe_data


class TestListRecipes:
    def test_list_recipes_empty(self, client):
        resp = client.get("/api/recipes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_recipes_returns_all(self, client):
        # Create two recipes
        client.post("/api/recipes", json=make_recipe_data(id="sambar", name="Sambar"))
        client.post("/api/recipes", json=make_recipe_data(id="avial", name="Avial"))

        resp = client.get("/api/recipes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Sorted alphabetically by name
        assert data[0]["id"] == "avial"
        assert data[1]["id"] == "sambar"

    def test_list_recipes_filter_by_cuisine(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="sambar", name="Sambar", cuisine_tags=["south_indian"]
        ))
        client.post("/api/recipes", json=make_recipe_data(
            id="palak", name="Palak Paneer", cuisine_tags=["north_indian"]
        ))

        resp = client.get("/api/recipes?cuisine=south_indian")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "sambar"

    def test_list_recipes_filter_by_template(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="sambar", name="Sambar", meal_template="south_indian"
        ))
        client.post("/api/recipes", json=make_recipe_data(
            id="khichdi", name="Khichdi", meal_template="comfort"
        ))

        resp = client.get("/api/recipes?template=comfort")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "khichdi"

    def test_list_recipes_filter_side_dishes(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="sambar", name="Sambar", is_side_dish=False
        ))
        client.post("/api/recipes", json=make_recipe_data(
            id="poriyal", name="Beans Poriyal", is_side_dish=True
        ))

        resp = client.get("/api/recipes?side_only=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "poriyal"

    def test_list_recipes_filter_main_dishes(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="sambar", name="Sambar", is_side_dish=False
        ))
        client.post("/api/recipes", json=make_recipe_data(
            id="poriyal", name="Beans Poriyal", is_side_dish=True
        ))

        resp = client.get("/api/recipes?side_only=false")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "sambar"

    def test_list_item_has_expected_fields(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="sambar", name="Sambar"))

        resp = client.get("/api/recipes")
        item = resp.json()[0]
        expected_fields = {
            "id", "name", "cuisine_tags", "meal_template", "is_side_dish",
            "protein_tier", "cook_familiarity", "serves",
            "prep_time_minutes", "cook_time_minutes",
        }
        assert expected_fields.issubset(set(item.keys()))
        # List items should NOT include heavy fields
        assert "ingredients" not in item
        assert "steps" not in item


class TestGetRecipe:
    def test_get_recipe_found(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="sambar", name="Sambar"))

        resp = client.get("/api/recipes/sambar")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "sambar"
        assert data["name"] == "Sambar"
        # Full detail includes ingredients and steps
        assert "ingredients" in data
        assert "steps" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_recipe_not_found(self, client):
        resp = client.get("/api/recipes/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_get_recipe_returns_all_fields(self, client):
        payload = make_recipe_data(
            id="full_test",
            name="Full Test",
            critical_notes="Important note",
            kid_adaptation="Less spicy",
            preferred_side_pairings=["beans_poriyal"],
            links=["https://example.com"],
        )
        client.post("/api/recipes", json=payload)

        resp = client.get("/api/recipes/full_test")
        data = resp.json()
        assert data["critical_notes"] == "Important note"
        assert data["kid_adaptation"] == "Less spicy"
        assert data["preferred_side_pairings"] == ["beans_poriyal"]
        assert data["links"] == ["https://example.com"]


class TestCreateRecipe:
    def test_create_recipe_success(self, client):
        payload = make_recipe_data(id="new_recipe", name="New Recipe")
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "new_recipe"
        assert data["name"] == "New Recipe"

    def test_create_recipe_duplicate_returns_409(self, client):
        payload = make_recipe_data(id="sambar", name="Sambar")
        client.post("/api/recipes", json=payload)

        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    def test_create_recipe_persists(self, client):
        payload = make_recipe_data(id="persist_test", name="Persist Test")
        client.post("/api/recipes", json=payload)

        resp = client.get("/api/recipes/persist_test")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Persist Test"

    def test_create_recipe_with_minimal_fields(self, client):
        payload = {"id": "minimal", "name": "Minimal Recipe"}
        resp = client.post("/api/recipes", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["protein_tier"] == "medium"  # default
        assert data["cook_familiarity"] == "needs_instructions"  # default
        assert data["ingredients"] == []
        assert data["steps"] == []

    def test_create_recipe_missing_name_returns_422(self, client):
        resp = client.post("/api/recipes", json={"id": "no_name"})
        assert resp.status_code == 422

    def test_create_recipe_missing_id_returns_422(self, client):
        resp = client.post("/api/recipes", json={"name": "No ID"})
        assert resp.status_code == 422


class TestUpdateRecipe:
    def test_update_recipe_name(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="update_test", name="Old Name"))

        resp = client.put("/api/recipes/update_test", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_recipe_partial(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="partial_test", name="Original", protein_tier="low"
        ))

        # Only update protein_tier, leave name unchanged
        resp = client.put("/api/recipes/partial_test", json={"protein_tier": "high"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["protein_tier"] == "high"
        assert data["name"] == "Original"  # unchanged

    def test_update_recipe_cook_familiarity(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="fam_test", cook_familiarity="new"
        ))

        resp = client.put("/api/recipes/fam_test", json={"cook_familiarity": "known"})
        assert resp.json()["cook_familiarity"] == "known"

    def test_update_recipe_cuisine_tags(self, client):
        client.post("/api/recipes", json=make_recipe_data(
            id="tag_test", cuisine_tags=["south_indian"]
        ))

        resp = client.put("/api/recipes/tag_test", json={
            "cuisine_tags": ["south_indian", "comfort"]
        })
        assert resp.json()["cuisine_tags"] == ["south_indian", "comfort"]

    def test_update_recipe_ingredients(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="ing_update"))

        new_ingredients = [
            {"name": "Paneer", "quantity": "200g", "category": "vegetable"}
        ]
        resp = client.put("/api/recipes/ing_update", json={"ingredients": new_ingredients})
        assert len(resp.json()["ingredients"]) == 1
        assert resp.json()["ingredients"][0]["name"] == "Paneer"

    def test_update_recipe_not_found(self, client):
        resp = client.put("/api/recipes/nonexistent", json={"name": "Nope"})
        assert resp.status_code == 404


class TestDeleteRecipe:
    def test_delete_recipe_success(self, client):
        client.post("/api/recipes", json=make_recipe_data(id="to_delete"))

        resp = client.delete("/api/recipes/to_delete")
        assert resp.status_code == 204

        # Verify it's gone
        resp = client.get("/api/recipes/to_delete")
        assert resp.status_code == 404

    def test_delete_recipe_not_found(self, client):
        resp = client.delete("/api/recipes/nonexistent")
        assert resp.status_code == 404
