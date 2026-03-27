"""Tests for the rules engine (Phase 1.2).

Tests each household hard constraint independently:
- Roti must be present
- Eggs must be present with style specified
- Salad must be present
- Main dish not repeated within last N days
- Follows correct meal template structure
"""

import pytest

from app.services.rules_engine import validate_plan, ValidationResult


def _make_plan(**overrides):
    """Helper to build a candidate meal plan dict."""
    defaults = {
        "template_id": "south_indian",
        "cuisine": "south_indian",
        "dishes": [
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
        ],
        "egg_style": "boiled",
        "roti_count": "standard batch",
        "include_curd_rice_side": False,
        "kid_notes": "Set aside dal for kid",
        "rationale": "Variety day",
    }
    defaults.update(overrides)
    return defaults


def _make_history(days: list[dict]) -> list[dict]:
    """Create meal history entries. Each entry: {date, dishes_cooked, egg_style, cuisine}."""
    return days


class TestRotiConstraint:
    """Roti must be included in every plan."""

    def test_plan_with_roti_passes(self):
        plan = _make_plan(roti_count="standard batch")
        result = validate_plan(plan, meal_history=[])
        assert result.roti_ok

    def test_plan_without_roti_fails(self):
        plan = _make_plan(roti_count="")
        result = validate_plan(plan, meal_history=[])
        assert not result.roti_ok
        assert any("roti" in v.lower() for v in result.violations)

    def test_plan_with_zero_roti_fails(self):
        plan = _make_plan(roti_count="0")
        result = validate_plan(plan, meal_history=[])
        assert not result.roti_ok


class TestEggConstraint:
    """Eggs must be present with a valid style."""

    def test_plan_with_eggs_passes(self):
        plan = _make_plan(egg_style="boiled")
        result = validate_plan(plan, meal_history=[])
        assert result.eggs_ok

    def test_plan_without_egg_style_fails(self):
        plan = _make_plan(egg_style="")
        result = validate_plan(plan, meal_history=[])
        assert not result.eggs_ok
        assert any("egg" in v.lower() for v in result.violations)

    def test_plan_with_invalid_egg_style_fails(self):
        plan = _make_plan(egg_style="poached")
        result = validate_plan(plan, meal_history=[])
        assert not result.eggs_ok


class TestSaladConstraint:
    """Salad must be present (all plans include it by default)."""

    def test_plan_with_salad_dish_passes(self):
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            {"recipe_id": "salad", "role": "salad", "name": "Carrots + Cucumber"},
        ])
        result = validate_plan(plan, meal_history=[])
        assert result.salad_ok

    def test_plan_without_salad_fails(self):
        """When there's no salad role in dishes and no separate salad flag."""
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        ])
        # We consider salad always included unless explicitly missing
        # But the plan should have salad in the plan structure
        result = validate_plan(plan, meal_history=[], require_salad_in_dishes=True)
        assert not result.salad_ok


class TestRepetitionConstraint:
    """Main dish must not repeat within last N days."""

    def test_no_repetition_passes(self):
        from datetime import date, timedelta
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        ])
        history = [
            {"date": yesterday, "dishes_cooked": ["palak_paneer"], "egg_style": "omelette", "cuisine": "north_indian"},
            {"date": two_days_ago, "dishes_cooked": ["avial"], "egg_style": "scrambled", "cuisine": "south_indian"},
        ]
        result = validate_plan(plan, meal_history=history, repetition_gap_days=3)
        assert result.repetition_ok

    def test_repetition_within_gap_fails(self):
        from datetime import date, timedelta
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        ])
        history = [
            {"date": yesterday, "dishes_cooked": ["sambar"], "egg_style": "boiled", "cuisine": "south_indian"},
        ]
        result = validate_plan(plan, meal_history=history, repetition_gap_days=3)
        assert not result.repetition_ok
        assert any("repeat" in v.lower() or "sambar" in v.lower() for v in result.violations)

    def test_repetition_outside_gap_passes(self):
        from datetime import date, timedelta
        five_days_ago = (date.today() - timedelta(days=5)).isoformat()
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        ])
        history = [
            {"date": five_days_ago, "dishes_cooked": ["sambar"], "egg_style": "boiled", "cuisine": "south_indian"},
        ]
        result = validate_plan(plan, meal_history=history, repetition_gap_days=3)
        assert result.repetition_ok

    def test_side_dish_repetition_allowed(self):
        """Side dishes can repeat — only main dishes are restricted."""
        from datetime import date, timedelta
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
        ])
        history = [
            {"date": yesterday, "dishes_cooked": ["beans_poriyal", "palak_paneer"], "egg_style": "omelette", "cuisine": "north_indian"},
        ]
        result = validate_plan(plan, meal_history=history, repetition_gap_days=3)
        assert result.repetition_ok


class TestTemplateStructure:
    """Plan must have at least a main dish."""

    def test_plan_with_main_dish_passes(self):
        plan = _make_plan(dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        ])
        result = validate_plan(plan, meal_history=[])
        assert result.template_ok

    def test_plan_without_main_dish_fails(self):
        plan = _make_plan(dishes=[
            {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
        ])
        result = validate_plan(plan, meal_history=[])
        assert not result.template_ok
        assert any("main" in v.lower() for v in result.violations)

    def test_empty_dishes_fails(self):
        plan = _make_plan(dishes=[])
        result = validate_plan(plan, meal_history=[])
        assert not result.template_ok


class TestOverallValidation:
    """Test the overall is_valid flag."""

    def test_valid_plan_passes_all(self):
        plan = _make_plan()
        result = validate_plan(plan, meal_history=[])
        assert result.is_valid
        assert len(result.violations) == 0

    def test_multiple_violations(self):
        plan = _make_plan(roti_count="", egg_style="", dishes=[])
        result = validate_plan(plan, meal_history=[])
        assert not result.is_valid
        assert len(result.violations) >= 3

    def test_validation_result_has_expected_fields(self):
        plan = _make_plan()
        result = validate_plan(plan, meal_history=[])
        assert isinstance(result, ValidationResult)
        assert hasattr(result, "is_valid")
        assert hasattr(result, "violations")
        assert hasattr(result, "roti_ok")
        assert hasattr(result, "eggs_ok")
        assert hasattr(result, "salad_ok")
        assert hasattr(result, "repetition_ok")
        assert hasattr(result, "template_ok")
