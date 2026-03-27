"""API integration tests for Meal Template endpoints."""

import json

from app.models.meal_template import MealTemplate
from tests.conftest import make_template_orm


class TestListTemplates:
    def test_list_templates_empty(self, client):
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_templates_returns_all(self, client, db_session):
        make_template_orm(db_session, id="south_indian", name="South Indian")
        make_template_orm(db_session, id="north_indian", name="North Indian")

        resp = client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_templates_sorted_by_name(self, client, db_session):
        make_template_orm(db_session, id="north_indian", name="North Indian")
        make_template_orm(db_session, id="bengali", name="Bengali")

        resp = client.get("/api/templates")
        data = resp.json()
        assert data[0]["name"] == "Bengali"
        assert data[1]["name"] == "North Indian"

    def test_template_has_expected_fields(self, client, db_session):
        make_template_orm(
            db_session,
            id="south_indian",
            name="South Indian",
            required_components=[{"role": "main_curry", "description": "Main curry"}],
            optional_components=[{"role": "side", "description": "Side dish"}],
            carb_rules={"default": "rice"},
            roti_rules={"shweta": "always"},
        )

        resp = client.get("/api/templates")
        tmpl = resp.json()[0]
        assert tmpl["id"] == "south_indian"
        assert tmpl["name"] == "South Indian"
        assert len(tmpl["required_components"]) == 1
        assert tmpl["required_components"][0]["role"] == "main_curry"
        assert len(tmpl["optional_components"]) == 1
        assert tmpl["carb_rules"]["default"] == "rice"
        assert tmpl["roti_rules"]["shweta"] == "always"
