"""Tests for cook brief familiarity enhancements (Phase 2.5).

Tests:
- known → short reminder (dish name + quantities + critical notes only)
- needs_instructions → full step-by-step
- new → full steps + YouTube link + pre-recorded audio note
- Familiarity toggle API endpoint
"""

from app.services.cook_brief import generate_cook_brief
from tests.conftest import make_recipe_orm


RECIPES_WITH_AUDIO = {
    "sambar": {
        "name": "Sambar",
        "cook_familiarity": "known",
        "critical_notes": "Roast 1.5 tbsp coriander seeds, 2 tsp chana dal, 13 red chilies",
        "steps": [
            {"order": 1, "instruction": "Pressure cook toor dal", "is_critical": False},
            {"order": 2, "instruction": "Roast masala and grind smooth", "is_critical": True},
            {"order": 3, "instruction": "Boil tamarind extract", "is_critical": False},
        ],
        "kid_adaptation": "Set aside dal before adding sambar masala",
        "links": [],
        "recipe_audio_url": None,
        "ingredients": [
            {"name": "Toor Dal", "quantity": "1 cup"},
            {"name": "Drumstick", "quantity": "200g"},
        ],
    },
    "palak_paneer": {
        "name": "Palak Paneer",
        "cook_familiarity": "needs_instructions",
        "critical_notes": "Blanch spinach in hot water for 2 min only",
        "steps": [
            {"order": 1, "instruction": "Blanch spinach and blend", "is_critical": False},
            {"order": 2, "instruction": "Sauté paneer cubes until golden", "is_critical": True},
            {"order": 3, "instruction": "Cook spinach paste with spices", "is_critical": False},
        ],
        "kid_adaptation": "Keep a mild portion for kid",
        "links": ["https://youtube.com/watch?v=example"],
        "recipe_audio_url": None,
        "ingredients": [
            {"name": "Spinach", "quantity": "500g"},
            {"name": "Paneer", "quantity": "200g"},
        ],
    },
    "schezwan_rice": {
        "name": "Schezwan Egg Fried Rice",
        "cook_familiarity": "new",
        "critical_notes": "",
        "steps": [
            {"order": 1, "instruction": "Cook rice and cool completely", "is_critical": False},
            {"order": 2, "instruction": "Add schezwan sauce and stir-fry on high heat", "is_critical": True},
        ],
        "kid_adaptation": "Set aside portion before adding sauce",
        "links": ["https://youtube.com/watch?v=friedrice"],
        "recipe_audio_url": "/api/audio/recipes/schezwan_rice.mp3",
        "ingredients": [
            {"name": "Rice", "quantity": "2 cups"},
            {"name": "Schezwan Sauce", "quantity": "3 tbsp"},
        ],
    },
}


class TestKnownRecipeBrief:
    """known → Short reminder only (dish name + quantities + critical notes)."""

    def test_known_shows_cook_knows_label(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "Cook knows this" in brief

    def test_known_shows_critical_notes(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "coriander seeds" in brief

    def test_known_shows_quantities(self):
        """Known recipes should include key quantities."""
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        # Quantities should appear (either in critical notes or dedicated section)
        assert "Toor Dal" in brief or "1 cup" in brief or "200g" in brief

    def test_known_does_not_show_full_steps(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "Pressure cook toor dal" not in brief


class TestNeedsInstructionsRecipeBrief:
    """needs_instructions → Full step-by-step."""

    def test_shows_all_steps(self):
        plan = {
            "dishes": [{"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "Blanch spinach" in brief
        assert "Sauté paneer" in brief

    def test_shows_kid_adaptation(self):
        plan = {
            "dishes": [{"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "Kid:" in brief or "kid" in brief.lower()

    def test_does_not_show_youtube_link(self):
        """needs_instructions should NOT show YouTube link (only new recipes do)."""
        plan = {
            "dishes": [{"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "youtube.com" not in brief


class TestNewRecipeBrief:
    """new → Full steps + YouTube link + pre-recorded audio note."""

    def test_shows_full_steps(self):
        plan = {
            "dishes": [{"recipe_id": "schezwan_rice", "role": "main", "name": "Schezwan Egg Fried Rice"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "Cook rice" in brief or "schezwan sauce" in brief.lower()

    def test_shows_youtube_link(self):
        plan = {
            "dishes": [{"recipe_id": "schezwan_rice", "role": "main", "name": "Schezwan Egg Fried Rice"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "youtube.com" in brief

    def test_shows_audio_available_note(self):
        """New recipe with recipe_audio_url should mention pre-recorded audio."""
        plan = {
            "dishes": [{"recipe_id": "schezwan_rice", "role": "main", "name": "Schezwan Egg Fried Rice"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, RECIPES_WITH_AUDIO)
        assert "pre-recorded" in brief.lower() or "audio" in brief.lower()


class TestFamiliarityToggleAPI:
    """Tests for PATCH /api/recipes/{id}/familiarity."""

    def test_toggle_to_known(self, client, db_session):
        recipe = make_recipe_orm(
            db_session, id="test_toggle", name="Test", cook_familiarity="needs_instructions"
        )
        resp = client.patch(
            f"/api/recipes/{recipe.id}/familiarity",
            json={"cook_familiarity": "known"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cook_familiarity"] == "known"

    def test_toggle_to_needs_instructions(self, client, db_session):
        recipe = make_recipe_orm(
            db_session, id="test_toggle2", name="Test2", cook_familiarity="known"
        )
        resp = client.patch(
            f"/api/recipes/{recipe.id}/familiarity",
            json={"cook_familiarity": "needs_instructions"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cook_familiarity"] == "needs_instructions"

    def test_toggle_404_for_missing_recipe(self, client):
        resp = client.patch(
            "/api/recipes/nonexistent/familiarity",
            json={"cook_familiarity": "known"},
        )
        assert resp.status_code == 404

    def test_toggle_rejects_invalid_value(self, client, db_session):
        recipe = make_recipe_orm(db_session, id="test_toggle3", name="Test3")
        resp = client.patch(
            f"/api/recipes/{recipe.id}/familiarity",
            json={"cook_familiarity": "invalid_value"},
        )
        assert resp.status_code == 422
