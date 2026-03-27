"""Tests for the Hindi Voice Script generation service (Phase 2.1).

Tests:
- Voice script prompt construction
- LLM response parsing
- Voice script API endpoint (generate + cache)
- Error handling when plan not found / not approved
"""

import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from app.models.meal_plan import MealPlan
from app.services.voice_script import (
    generate_voice_script,
    _build_voice_script_prompt,
)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PLAN = {
    "plan_date": "2026-02-16",
    "cuisine": "South Indian",
    "dishes": [
        {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
    ],
    "egg_style": "omelette",
    "roti_count": "standard batch",
    "include_curd_rice_side": False,
    "kid_notes": "Set aside dal before adding sambar masala. No chili in omelette.",
}

SAMPLE_RECIPES = {
    "sambar": {
        "name": "Sambar",
        "cook_familiarity": "known",
        "critical_notes": "Roast 1.5 tbsp coriander seeds, 2 tsp chana dal, 13 red chilies",
        "steps": [
            {"order": 1, "instruction": "Pressure cook toor dal", "is_critical": False},
            {"order": 2, "instruction": "Roast masala and grind smooth", "is_critical": True},
        ],
        "kid_adaptation": "Set aside dal before adding sambar masala",
        "ingredients": [
            {"name": "Toor Dal", "quantity": "1 cup"},
            {"name": "Drumstick", "quantity": "200g"},
        ],
    },
    "beans_poriyal": {
        "name": "Beans Poriyal",
        "cook_familiarity": "known",
        "critical_notes": "Don't overcook the beans",
        "steps": [
            {"order": 1, "instruction": "Chop beans finely", "is_critical": False},
            {"order": 2, "instruction": "Sauté with mustard, urad dal", "is_critical": False},
        ],
        "kid_adaptation": "",
        "ingredients": [
            {"name": "French Beans", "quantity": "250g"},
        ],
    },
}

SAMPLE_LEFTOVERS = [
    {"dish_name": "Yesterday's rasam", "servings_estimate": "small"},
]


# ---------------------------------------------------------------------------
# Prompt construction tests
# ---------------------------------------------------------------------------


class TestVoiceScriptPromptConstruction:
    """Tests for building the LLM prompt for voice script generation."""

    def test_prompt_includes_dish_names(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=SAMPLE_LEFTOVERS
        )
        assert "Sambar" in prompt
        assert "Beans Poriyal" in prompt

    def test_prompt_includes_egg_style(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "omelette" in prompt.lower()

    def test_prompt_includes_quantities(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "Toor Dal" in prompt or "toor dal" in prompt.lower()

    def test_prompt_includes_kid_notes(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "kid" in prompt.lower() or "baby" in prompt.lower() or "bacche" in prompt.lower()

    def test_prompt_includes_leftover_notes(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=SAMPLE_LEFTOVERS
        )
        assert "rasam" in prompt.lower()

    def test_prompt_includes_critical_steps(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "coriander seeds" in prompt.lower() or "critical" in prompt.lower()

    def test_prompt_includes_roti_info(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "roti" in prompt.lower()

    def test_prompt_requests_hindi(self):
        """The prompt should explicitly request Hindi output."""
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "hindi" in prompt.lower() or "Hindi" in prompt

    def test_prompt_uses_generic_household_language(self):
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "Planner One" not in prompt
        assert "Planner Two" not in prompt
        assert "5 total" in prompt

    def test_prompt_targets_spoken_style(self):
        """The prompt should request spoken/conversational style."""
        prompt = _build_voice_script_prompt(
            SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
        )
        assert "spoken" in prompt.lower() or "conversational" in prompt.lower()


# ---------------------------------------------------------------------------
# Service tests (mock LLM)
# ---------------------------------------------------------------------------


class TestVoiceScriptGeneration:
    """Tests for the generate_voice_script function with mocked LLM."""

    MOCK_HINDI_SCRIPT = (
        "Namaste! Kal ke liye: sambar banani hai drumstick aur tomato ke saath. "
        "Saath mein beans poriyal. Roti regular batch. "
        "Ande — omelette banana hai, paanch ande."
    )

    @pytest.mark.asyncio
    async def test_generates_hindi_script(self):
        """Should return a Hindi script string from the LLM."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = self.MOCK_HINDI_SCRIPT

        with patch(
            "app.services.voice_script.AsyncAzureOpenAI"
        ) as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            result = await generate_voice_script(
                SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=SAMPLE_LEFTOVERS
            )

        assert isinstance(result, str)
        assert len(result) > 0
        assert "sambar" in result.lower()

    @pytest.mark.asyncio
    async def test_returns_script_text_directly(self):
        """The returned script should be the raw text from the LLM, not JSON."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = self.MOCK_HINDI_SCRIPT

        with patch(
            "app.services.voice_script.AsyncAzureOpenAI"
        ) as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_response)
            MockClient.return_value = instance

            result = await generate_voice_script(
                SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
            )

        # Should be plain text, not JSON
        assert not result.startswith("{")
        assert not result.startswith("[")

    @pytest.mark.asyncio
    async def test_raises_on_llm_failure(self):
        """Should propagate LLM errors."""
        with patch(
            "app.services.voice_script.AsyncAzureOpenAI"
        ) as MockClient:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(
                side_effect=Exception("Azure API error")
            )
            MockClient.return_value = instance

            with pytest.raises(Exception, match="Azure API error"):
                await generate_voice_script(
                    SAMPLE_PLAN, SAMPLE_RECIPES, leftovers=[]
                )


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestVoiceScriptAPI:
    """Tests for GET /api/voice-script/{plan_id}."""

    def _create_approved_plan(self, db_session) -> MealPlan:
        """Helper to create an approved plan in the test DB."""
        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="approved",
            template_id="south_indian",
            cuisine="South Indian",
            egg_style="omelette",
            roti_count="standard batch",
            kid_notes="Less spicy for kid",
            rationale="Test plan",
        )
        plan.set_dishes([
            {"recipe_id": "test_dish", "role": "main", "name": "Test Dish"},
        ])
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        return plan

    def test_returns_cached_script(self, client, db_session):
        """If voice_script_text is already set, return it without calling LLM."""
        plan = self._create_approved_plan(db_session)
        plan.voice_script_text = "Cached Hindi script"
        db_session.commit()

        resp = client.get(f"/api/voice-script/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"] == plan.id
        assert data["script_text"] == "Cached Hindi script"

    def test_404_for_nonexistent_plan(self, client):
        resp = client.get("/api/voice-script/99999")
        assert resp.status_code == 404

    def test_400_for_non_approved_plan(self, client, db_session):
        """Voice script should only be generated for approved plans."""
        plan = MealPlan(
            plan_date=date.today() + timedelta(days=1),
            status="draft",
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

        resp = client.get(f"/api/voice-script/{plan.id}")
        assert resp.status_code == 400

    @patch("app.routers.voice.generate_voice_script", new_callable=AsyncMock)
    def test_generates_and_caches_script(self, mock_gen, client, db_session):
        """Should call generate_voice_script and cache result on MealPlan."""
        mock_gen.return_value = "Namaste! Kal ke liye sambar banani hai."

        plan = self._create_approved_plan(db_session)
        resp = client.get(f"/api/voice-script/{plan.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["script_text"] == "Namaste! Kal ke liye sambar banani hai."

        # Verify it was cached
        db_session.refresh(plan)
        assert plan.voice_script_text == "Namaste! Kal ke liye sambar banani hai."
