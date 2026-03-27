"""Tests for the Cook Brief generation service (Phase 1.4 + Phase 2 enhancements).

Tests:
- Brief includes menu overview
- Brief respects cook_familiarity levels
- Brief includes kid notes
- Brief includes leftover notes
- Brief includes ingredient quantities for known recipes
- Brief includes pre-recorded audio note for new recipes
- Brief API endpoint (including voice data in response)
"""

from app.services.cook_brief import generate_cook_brief


SAMPLE_RECIPES = {
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
        "ingredients": [
            {"name": "Toor Dal", "quantity": "1 cup", "category": "pantry"},
            {"name": "Drumstick", "quantity": "2 sticks", "category": "vegetable"},
            {"name": "Tomato", "quantity": "2 medium", "category": "vegetable"},
        ],
        "recipe_audio_url": None,
    },
    "palak_paneer": {
        "name": "Palak Paneer",
        "cook_familiarity": "needs_instructions",
        "critical_notes": "",
        "steps": [
            {"order": 1, "instruction": "Blanch spinach and blend", "is_critical": False},
            {"order": 2, "instruction": "Sauté paneer cubes", "is_critical": True},
            {"order": 3, "instruction": "Cook spinach paste with spices", "is_critical": False},
        ],
        "kid_adaptation": "Keep a mild portion for kid",
        "links": ["https://youtube.com/watch?v=example"],
        "ingredients": [],
        "recipe_audio_url": None,
    },
    "beans_poriyal": {
        "name": "Beans Poriyal",
        "cook_familiarity": "known",
        "critical_notes": "Don't overcook the beans",
        "steps": [
            {"order": 1, "instruction": "Chop beans finely", "is_critical": False},
            {"order": 2, "instruction": "Sauté with mustard, urad dal, curry leaves", "is_critical": False},
        ],
        "kid_adaptation": "",
        "links": [],
        "ingredients": [
            {"name": "French Beans", "quantity": "250g", "category": "vegetable"},
        ],
        "recipe_audio_url": None,
    },
    "schezwan_rice": {
        "name": "Schezwan Egg Fried Rice",
        "cook_familiarity": "new",
        "critical_notes": "",
        "steps": [
            {"order": 1, "instruction": "Cook rice and cool", "is_critical": False},
            {"order": 2, "instruction": "Add schezwan sauce and stir-fry", "is_critical": True},
        ],
        "kid_adaptation": "Set aside portion before adding sauce",
        "links": ["https://youtube.com/watch?v=friedrice"],
        "ingredients": [],
        "recipe_audio_url": "/api/audio/recipes/schezwan_rice.mp3",
    },
}


class TestCookBriefMenuOverview:
    def test_includes_menu_items(self):
        plan = {
            "plan_date": "2026-02-16",
            "cuisine": "South Indian",
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
                {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
            ],
            "egg_style": "omelette",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Sambar" in brief
        assert "Beans Poriyal" in brief
        assert "TODAY'S MENU" in brief

    def test_includes_egg_style(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "scrambled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Scrambled" in brief
        assert "5 eggs total" in brief
        assert "Planner One" not in brief

    def test_includes_roti_count(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch + 5 extra",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "5 extra" in brief

    def test_includes_curd_rice_when_enabled(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "include_curd_rice_side": True,
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "optional curd rice side" in brief.lower()

    def test_includes_salad(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Salad" in brief
        assert "Carrots" in brief


class TestCookBriefFamiliarityLevels:
    def test_known_recipe_abbreviated(self):
        """Known recipes should show only critical notes, not full steps."""
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Cook knows this" in brief
        assert "coriander seeds" in brief
        # Should NOT include numbered step instructions for known recipes
        assert "Pressure cook toor dal" not in brief

    def test_known_recipe_shows_ingredient_quantities(self):
        """Known recipes should include key quantities as a reminder."""
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Quantities" in brief
        assert "Toor Dal" in brief
        assert "1 cup" in brief

    def test_needs_instructions_shows_full_steps(self):
        """needs_instructions recipes should show all steps."""
        plan = {
            "dishes": [{"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Blanch spinach" in brief
        assert "Sauté paneer" in brief
        assert "Kid:" in brief

    def test_new_recipe_shows_video_link(self):
        """New recipes should show video link if available."""
        plan = {
            "dishes": [{"recipe_id": "schezwan_rice", "role": "main", "name": "Schezwan Egg Fried Rice"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "youtube.com" in brief

    def test_new_recipe_shows_prerecorded_audio_note(self):
        """New recipes with pre-recorded audio should show audio available note."""
        plan = {
            "dishes": [{"recipe_id": "schezwan_rice", "role": "main", "name": "Schezwan Egg Fried Rice"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "Pre-recorded audio" in brief


class TestCookBriefKidNotes:
    def test_includes_plan_level_kid_notes(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "Set aside dal for kid. No chili in omelette.",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES)
        assert "KID NOTE" in brief
        assert "Set aside dal" in brief


class TestCookBriefLeftoverNotes:
    def test_includes_leftover_notes(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        leftovers = [{"dish_name": "Yesterday's rasam", "servings_estimate": "small"}]
        brief = generate_cook_brief(plan, SAMPLE_RECIPES, leftovers=leftovers)
        assert "LEFTOVER NOTE" in brief
        assert "rasam" in brief

    def test_no_leftover_section_when_empty(self):
        plan = {
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "boiled",
            "roti_count": "standard batch",
            "kid_notes": "",
        }
        brief = generate_cook_brief(plan, SAMPLE_RECIPES, leftovers=[])
        assert "LEFTOVER NOTE" not in brief


class TestCookBriefAPI:
    """Tests for GET /api/brief/{plan_id}."""

    def test_get_brief_for_approved_plan(self, client, db_session):
        """Should return cook brief text for an approved plan."""
        from datetime import date, timedelta
        from app.models.meal_plan import MealPlan

        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            egg_style="omelette",
            roti_count="standard batch",
            kid_notes="Less spicy for kid",
            rationale="Test",
        )
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        resp = client.get(f"/api/brief/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "brief_text" in data
        assert "COOK BRIEF" in data["brief_text"]
        assert "Test Dish" in data["brief_text"]

    def test_get_brief_for_nonexistent_plan(self, client):
        resp = client.get("/api/brief/99999")
        assert resp.status_code == 404

    def test_brief_response_includes_voice_data_when_cached(self, client, db_session):
        """Brief response should include voice_audio_url and voice_script_text when available."""
        from datetime import date, timedelta
        from app.models.meal_plan import MealPlan

        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            egg_style="omelette",
            roti_count="standard batch",
            kid_notes="",
            rationale="Test",
            cook_brief_text="Cached brief text",
            voice_script_text="Hindi script text here",
            voice_audio_url="/api/audio/brief_42.mp3",
        )
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        resp = client.get(f"/api/brief/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["brief_text"] == "Cached brief text"
        assert data["voice_audio_url"] == "/api/audio/brief_42.mp3"
        assert data["voice_script_text"] == "Hindi script text here"

    def test_brief_response_voice_data_null_when_not_generated(self, client, db_session):
        """Brief response should have null voice fields when voice not yet generated."""
        from datetime import date, timedelta
        from app.models.meal_plan import MealPlan

        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            egg_style="omelette",
            roti_count="standard batch",
            kid_notes="",
            rationale="Test",
        )
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        resp = client.get(f"/api/brief/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["voice_audio_url"] is None
        assert data["voice_script_text"] is None
