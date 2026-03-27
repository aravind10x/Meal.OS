"""API integration tests for reference data endpoints (vegetables, pantry staples)."""

from tests.conftest import make_household_orm


class TestVegetablesEndpoint:
    def test_list_vegetables_returns_data(self, client):
        resp = client.get("/api/vegetables")
        assert resp.status_code == 200
        data = resp.json()
        # vegetables.json has categorized vegetable lists under "vegetables"
        assert "vegetables" in data
        assert len(data["vegetables"]) > 0

    def test_vegetables_have_names(self, client):
        resp = client.get("/api/vegetables")
        data = resp.json()
        for category in data["vegetables"]:
            assert "category" in category
            assert "items" in category
            assert len(category["items"]) > 0
            for item in category["items"]:
                assert "name" in item

    def test_vegetables_include_poriyal_category(self, client):
        """Verify the well-known 'Poriyal / Stir-fry' category exists."""
        resp = client.get("/api/vegetables")
        data = resp.json()
        category_names = [c["category"] for c in data["vegetables"]]
        assert any("poriyal" in name.lower() or "stir" in name.lower() for name in category_names)


class TestPantryStaplesEndpoint:
    def test_pantry_staples_from_household(self, client, db_session):
        """When a household profile exists, return its pantry staples."""
        make_household_orm(
            db_session, pantry_staples=["salt", "rice", "oil"]
        )

        resp = client.get("/api/pantry-staples")
        assert resp.status_code == 200
        data = resp.json()
        assert "pantry_staples" in data
        assert "salt" in data["pantry_staples"]

    def test_pantry_staples_fallback_to_json(self, client):
        """When no household profile exists, fall back to JSON seed file as flat list."""
        resp = client.get("/api/pantry-staples")
        assert resp.status_code == 200
        data = resp.json()
        assert "pantry_staples" in data
        # Fallback must return a flat list of strings (consistent with DB-backed response)
        items = data["pantry_staples"]
        assert isinstance(items, list)
        assert len(items) > 0
        assert all(isinstance(item, str) for item in items)


class TestHealthEndpoint:
    def test_health_check(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["app"] == "Meal.OS"
        assert "version" in data
