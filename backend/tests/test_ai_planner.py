"""Tests for the AI Planner service (Phase 1.2).

Uses mocked Azure OpenAI responses for unit tests.
Optional integration test with real Azure OpenAI (marked with pytest.mark.integration).
"""

import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_planner import (
    _build_system_prompt,
    _build_user_prompt,
    _parse_ai_response,
    generate_meal_plans,
)


# ---------------------------------------------------------------------------
# Test data fixtures
# ---------------------------------------------------------------------------

SAMPLE_TEMPLATES = [
    {
        "id": "south_indian",
        "name": "South Indian",
        "required_components": [{"role": "main_curry"}, {"role": "carb"}],
        "roti_rules": {"roti_preferred_member": "always"},
    },
    {
        "id": "north_indian",
        "name": "North Indian",
        "required_components": [{"role": "curry"}, {"role": "carb"}],
        "roti_rules": {"extra_rotis_for_high_appetite_member": True, "extra_count": 5},
    },
]

SAMPLE_RECIPES = [
    {"id": "sambar", "name": "Sambar", "cuisine_tags": ["south_indian"], "is_side_dish": False,
     "protein_tier": "medium", "cook_familiarity": "known", "preferred_side_pairings": ["beans_poriyal"]},
    {"id": "palak_paneer", "name": "Palak Paneer", "cuisine_tags": ["north_indian"], "is_side_dish": False,
     "protein_tier": "high", "cook_familiarity": "needs_instructions", "preferred_side_pairings": []},
    {"id": "beans_poriyal", "name": "Beans Poriyal", "cuisine_tags": ["south_indian"], "is_side_dish": True,
     "protein_tier": "low", "cook_familiarity": "known", "preferred_side_pairings": []},
]

SAMPLE_HISTORY = [
    {"date": (date.today() - timedelta(days=1)).isoformat(), "dishes_cooked": ["avial"], "egg_style": "boiled", "cuisine": "south_indian"},
    {"date": (date.today() - timedelta(days=2)).isoformat(), "dishes_cooked": ["palak_paneer"], "egg_style": "omelette", "cuisine": "north_indian"},
]

MOCK_AI_RESPONSE = json.dumps({
    "plans": [
        {
            "template_id": "south_indian",
            "cuisine": "South Indian",
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
                {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
            ],
            "egg_style": "scrambled",
            "include_curd_rice_side": False,
            "roti_count": "standard batch",
            "kid_notes": "Set aside dal for kid",
            "rationale": "Uses drumstick. Different from yesterday.",
            "missing_ingredients": ["Drumstick"],
        },
        {
            "template_id": "north_indian",
            "cuisine": "North Indian",
            "dishes": [
                {"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"},
            ],
            "egg_style": "fried",
            "include_curd_rice_side": True,
            "roti_count": "standard batch + 5 extra",
            "kid_notes": "Make one portion mild",
            "rationale": "High protein. Palak paneer not made recently.",
            "missing_ingredients": ["Paneer", "Spinach"],
        },
        {
            "template_id": "south_indian",
            "cuisine": "South Indian",
            "dishes": [
                {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            ],
            "egg_style": "omelette",
            "include_curd_rice_side": False,
            "roti_count": "standard batch",
            "kid_notes": "Less spicy sambar for kid",
            "rationale": "Simple comfort meal.",
            "missing_ingredients": [],
        },
    ]
})


# ---------------------------------------------------------------------------
# Prompt building tests
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_includes_template_info(self):
        prompt = _build_system_prompt(SAMPLE_TEMPLATES, SAMPLE_RECIPES, [])
        assert "south_indian" in prompt
        assert "north_indian" in prompt

    def test_includes_recipe_info(self):
        prompt = _build_system_prompt(SAMPLE_TEMPLATES, SAMPLE_RECIPES, [])
        assert "sambar" in prompt
        assert "Palak Paneer" in prompt

    def test_includes_history(self):
        prompt = _build_system_prompt(SAMPLE_TEMPLATES, SAMPLE_RECIPES, SAMPLE_HISTORY)
        assert "avial" in prompt
        assert "boiled" in prompt

    def test_handles_empty_data(self):
        prompt = _build_system_prompt([], [], [])
        assert "No templates loaded" in prompt
        assert "No recipes loaded" in prompt
        assert "No history yet" in prompt


class TestBuildUserPrompt:
    def test_includes_vegetables(self):
        prompt = _build_user_prompt(
            date.today(), ["Beans", "Drumstick"], ["Drumstick"], []
        )
        assert "Beans" in prompt
        assert "Drumstick" in prompt

    def test_includes_use_soon(self):
        prompt = _build_user_prompt(
            date.today(), ["Beans"], ["Beans"], []
        )
        assert "Beans" in prompt

    def test_includes_leftovers(self):
        prompt = _build_user_prompt(
            date.today(), [], [], [{"dish_name": "Sambar", "servings_estimate": "small"}]
        )
        assert "Sambar" in prompt

    def test_handles_no_leftovers(self):
        prompt = _build_user_prompt(date.today(), ["Beans"], [], [])
        assert "None" in prompt


# ---------------------------------------------------------------------------
# Response parsing tests
# ---------------------------------------------------------------------------

class TestParseAIResponse:
    def test_parses_valid_json(self):
        plans = _parse_ai_response(MOCK_AI_RESPONSE)
        assert len(plans) == 3
        assert plans[0]["template_id"] == "south_indian"

    def test_handles_markdown_fences(self):
        wrapped = f"```json\n{MOCK_AI_RESPONSE}\n```"
        plans = _parse_ai_response(wrapped)
        assert len(plans) == 3

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            _parse_ai_response("not json at all")

    def test_raises_on_missing_plans_key(self):
        with pytest.raises(ValueError, match="missing 'plans' array"):
            _parse_ai_response('{"meals": []}')


# ---------------------------------------------------------------------------
# generate_meal_plans (mocked) tests
# ---------------------------------------------------------------------------

class TestGenerateMealPlansMocked:
    @pytest.mark.asyncio
    async def test_returns_validated_plans(self):
        """Mocked Azure OpenAI returns 3 plans, all validated."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = MOCK_AI_RESPONSE

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.ai_planner.AsyncAzureOpenAI", return_value=mock_client):
            plans = await generate_meal_plans(
                plan_date=date.today() + timedelta(days=1),
                vegetables=["Beans", "Drumstick"],
                use_soon=["Drumstick"],
                leftovers=[],
                templates=SAMPLE_TEMPLATES,
                recipes=SAMPLE_RECIPES,
                history=SAMPLE_HISTORY,
            )

        assert len(plans) == 3
        # Each plan should have validation info
        for plan in plans:
            assert "validation" in plan
            assert "is_valid" in plan["validation"]
            assert "violations" in plan["validation"]

    @pytest.mark.asyncio
    async def test_detects_rule_violations(self):
        """Plans missing roti/eggs should be flagged by rules engine."""
        bad_response = json.dumps({
            "plans": [{
                "template_id": "south_indian",
                "cuisine": "South Indian",
                "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
                "egg_style": "",  # Missing egg style
                "roti_count": "",  # Missing roti
                "kid_notes": "",
                "rationale": "Test",
                "missing_ingredients": [],
            }]
        })

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = bad_response

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.ai_planner.AsyncAzureOpenAI", return_value=mock_client):
            plans = await generate_meal_plans(
                plan_date=date.today() + timedelta(days=1),
                vegetables=[], use_soon=[], leftovers=[],
                templates=SAMPLE_TEMPLATES, recipes=SAMPLE_RECIPES, history=[],
            )

        assert len(plans) == 1
        assert not plans[0]["validation"]["is_valid"]
        assert len(plans[0]["validation"]["violations"]) >= 2


# ---------------------------------------------------------------------------
# Integration test with real Azure OpenAI (optional, requires API key)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_plans_real_azure():
    """Integration test: actually call Azure OpenAI to generate plans.

    Run with: pytest tests/test_ai_planner.py -v -m integration
    Requires AZURE_OPENAI_API_KEY to be set in .env
    """
    from app.config import settings

    if not settings.AZURE_OPENAI_API_KEY:
        pytest.skip("AZURE_OPENAI_API_KEY not set — skipping integration test")

    plans = await generate_meal_plans(
        plan_date=date.today() + timedelta(days=1),
        vegetables=["French Beans", "Drumstick", "Spinach"],
        use_soon=["Spinach"],
        leftovers=[{"dish_name": "Yesterday's dal", "servings_estimate": "small"}],
        templates=SAMPLE_TEMPLATES,
        recipes=SAMPLE_RECIPES,
        history=SAMPLE_HISTORY,
    )

    assert len(plans) >= 2
    for plan in plans:
        assert "template_id" in plan
        assert "dishes" in plan
        assert "egg_style" in plan
        assert "validation" in plan
