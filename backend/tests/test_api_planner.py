"""Tests for the Planner API (Phase 1.2-1.3).

Covers:
- POST /api/planner/generate — generate meal plan candidates (mocked AI)
- GET /api/planner/candidates — get draft candidates (with validation info)
- GET /api/planner/approved — get approved plan for a date
- POST /api/planner/approve/{plan_id} — approve a plan (with validation enforcement)
- POST /api/planner/swap — swap a dish in a plan (with recipe validation)
- GET /api/meal-history — get meal history
- Leftover expiry — stale leftovers auto-expired
- Multiple approval — supersedes previous approved plans
"""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.meal_plan import MealPlan
from app.models.meal_history import MealHistory
from app.models.leftover import Leftover
from app.models.recipe import Recipe
from tests.conftest import make_recipe_orm


# ---------------------------------------------------------------------------
# Helpers: create draft plans directly in the DB (bypasses AI)
# ---------------------------------------------------------------------------

def _create_draft_plan(client, db_session, plan_date=None, **overrides):
    """Insert a draft MealPlan into the test DB and return its id."""
    if plan_date is None:
        plan_date = date.today() + timedelta(days=1)

    plan = MealPlan(
        plan_date=plan_date,
        status="draft",
        template_id=overrides.get("template_id", "south_indian"),
        cuisine=overrides.get("cuisine", "South Indian"),
        egg_style=overrides.get("egg_style", "boiled"),
        include_curd_rice_side=overrides.get("include_curd_rice_side", False),
        roti_count=overrides.get("roti_count", "standard batch"),
        kid_notes=overrides.get("kid_notes", "Set aside dal for kid"),
        rationale=overrides.get("rationale", "Test plan"),
    )
    plan.set_dishes(overrides.get("dishes", [
        {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
    ]))
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan.id


def _create_approved_plan(client, db_session, plan_date=None, **overrides):
    """Insert an approved MealPlan into the test DB and return its id."""
    if plan_date is None:
        plan_date = date.today() + timedelta(days=1)

    plan = MealPlan(
        plan_date=plan_date,
        status="approved",
        template_id=overrides.get("template_id", "south_indian"),
        cuisine=overrides.get("cuisine", "South Indian"),
        egg_style=overrides.get("egg_style", "boiled"),
        include_curd_rice_side=overrides.get("include_curd_rice_side", False),
        roti_count=overrides.get("roti_count", "standard batch"),
        kid_notes=overrides.get("kid_notes", "Set aside dal for kid"),
        rationale=overrides.get("rationale", "Test plan"),
        approved_at=datetime.now(timezone.utc),
    )
    plan.set_dishes(overrides.get("dishes", [
        {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
        {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
    ]))
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan.id


# We need a db_session that uses the same engine as the client
@pytest.fixture
def plan_db(db_engine):
    """Provide a session that shares the test engine."""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# POST /api/planner/generate (mocked AI)
# ---------------------------------------------------------------------------

class TestGeneratePlans:
    def test_generate_creates_draft_plans(self, client, plan_db):
        """Mocked AI → should store 3 draft plans in DB."""
        mock_plans = [
            {
                "template_id": "south_indian",
                "cuisine": "South Indian",
                "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
                "egg_style": "scrambled",
                "roti_count": "standard batch",
                "kid_notes": "Less spicy",
                "rationale": "Test",
                "missing_ingredients": [],
                "validation": {"is_valid": True, "violations": []},
            },
            {
                "template_id": "north_indian",
                "cuisine": "North Indian",
                "dishes": [{"recipe_id": "palak_paneer", "role": "main", "name": "Palak Paneer"}],
                "egg_style": "fried",
                "roti_count": "standard + 5 extra",
                "kid_notes": "Mild portion",
                "rationale": "High protein",
                "missing_ingredients": ["Paneer"],
                "validation": {"is_valid": True, "violations": []},
            },
        ]

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        with patch("app.routers.planner.generate_meal_plans", new_callable=AsyncMock, return_value=mock_plans):
            resp = client.post("/api/planner/generate", json={
                "plan_date": tomorrow,
                "vegetables": ["Beans"],
                "use_soon": [],
                "leftovers": [],
            })

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["status"] == "draft"
        assert data[0]["template_id"] == "south_indian"
        assert data[1]["template_id"] == "north_indian"


# ---------------------------------------------------------------------------
# GET /api/planner/candidates
# ---------------------------------------------------------------------------

class TestGetCandidates:
    def test_returns_draft_plans(self, client, plan_db):
        """Should return all draft plans."""
        tomorrow = date.today() + timedelta(days=1)
        _create_draft_plan(client, plan_db, plan_date=tomorrow)
        _create_draft_plan(client, plan_db, plan_date=tomorrow, template_id="north_indian")

        resp = client.get(f"/api/planner/candidates?plan_date={tomorrow.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_returns_empty_when_no_drafts(self, client):
        resp = client.get("/api/planner/candidates")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_candidates_include_validation_info(self, client, plan_db):
        """Candidates should include validation info from rules engine."""
        tomorrow = date.today() + timedelta(days=1)
        _create_draft_plan(client, plan_db, plan_date=tomorrow)

        resp = client.get(f"/api/planner/candidates?plan_date={tomorrow.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "validation" in data[0]
        assert "is_valid" in data[0]["validation"]
        assert "violations" in data[0]["validation"]

    def test_candidates_does_not_include_approved_plans(self, client, plan_db):
        """Candidates endpoint should only return drafts, not approved plans."""
        tomorrow = date.today() + timedelta(days=1)
        _create_draft_plan(client, plan_db, plan_date=tomorrow)
        _create_approved_plan(client, plan_db, plan_date=tomorrow, template_id="north_indian")

        resp = client.get(f"/api/planner/candidates?plan_date={tomorrow.isoformat()}")
        data = resp.json()
        assert len(data) == 1
        assert all(p["status"] == "draft" for p in data)


# ---------------------------------------------------------------------------
# GET /api/planner/approved
# ---------------------------------------------------------------------------

class TestGetApprovedPlan:
    def test_returns_approved_plan(self, client, plan_db):
        """Should return the approved plan for a given date."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_approved_plan(client, plan_db, plan_date=tomorrow)

        resp = client.get(f"/api/planner/approved?plan_date={tomorrow.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        assert data["id"] == plan_id
        assert data["status"] == "approved"

    def test_returns_null_when_no_approved(self, client):
        """Should return null (empty body) when no approved plan exists."""
        tomorrow = date.today() + timedelta(days=1)
        resp = client.get(f"/api/planner/approved?plan_date={tomorrow.isoformat()}")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_most_recent_approved(self, client, plan_db):
        """When multiple approved plans exist (pre-fix data), returns the latest."""
        tomorrow = date.today() + timedelta(days=1)
        _create_approved_plan(client, plan_db, plan_date=tomorrow, template_id="south_indian")
        latest_id = _create_approved_plan(client, plan_db, plan_date=tomorrow, template_id="north_indian")

        resp = client.get(f"/api/planner/approved?plan_date={tomorrow.isoformat()}")
        data = resp.json()
        assert data["id"] == latest_id

    def test_invalid_date_format_returns_400(self, client):
        resp = client.get("/api/planner/approved?plan_date=not-a-date")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/planner/approve/{plan_id}
# ---------------------------------------------------------------------------

class TestApprovePlan:
    def test_approve_sets_status_and_records_history(self, client, plan_db):
        """Approving a plan should set status=approved and create a history entry."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        resp = client.post(f"/api/planner/approve/{plan_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"]["status"] == "approved"
        assert data["plan"]["approved_at"] is not None
        assert data["history_recorded"] is True

    def test_approve_discards_other_drafts(self, client, plan_db):
        """Approving one plan should discard other drafts for the same date."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id_1 = _create_draft_plan(client, plan_db, plan_date=tomorrow)
        plan_id_2 = _create_draft_plan(client, plan_db, plan_date=tomorrow, template_id="north_indian")

        # Approve plan 1
        resp = client.post(f"/api/planner/approve/{plan_id_1}")
        assert resp.status_code == 200

        # Check plan 2 is no longer draft
        plan2 = plan_db.query(MealPlan).filter(MealPlan.id == plan_id_2).first()
        plan_db.refresh(plan2)
        assert plan2.status == "discarded"

    def test_approve_nonexistent_plan_returns_404(self, client):
        resp = client.post("/api/planner/approve/99999")
        assert resp.status_code == 404

    def test_approve_already_approved_returns_400(self, client, plan_db):
        """Approving an already-approved plan should return 400."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        client.post(f"/api/planner/approve/{plan_id}")
        resp = client.post(f"/api/planner/approve/{plan_id}")
        assert resp.status_code == 400

    def test_approve_marks_leftovers_consumed(self, client, plan_db):
        """On approval, active leftovers for that date should be marked consumed."""
        tomorrow = date.today() + timedelta(days=1)

        # Create a leftover
        lo = Leftover(
            dish_name="Dal", servings_estimate="small",
            date_logged=tomorrow, status="active"
        )
        plan_db.add(lo)
        plan_db.commit()

        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)
        client.post(f"/api/planner/approve/{plan_id}")

        # Check leftover
        plan_db.refresh(lo)
        assert lo.status == "consumed"

    def test_approve_supersedes_existing_approved_plan(self, client, plan_db):
        """Approving a new plan should supersede the existing approved plan for that date."""
        tomorrow = date.today() + timedelta(days=1)

        # Create an already-approved plan
        old_approved_id = _create_approved_plan(client, plan_db, plan_date=tomorrow)

        # Create a new draft and approve it
        new_draft_id = _create_draft_plan(client, plan_db, plan_date=tomorrow, template_id="north_indian")
        resp = client.post(f"/api/planner/approve/{new_draft_id}")
        assert resp.status_code == 200

        # Old approved plan should now be superseded
        old_plan = plan_db.query(MealPlan).filter(MealPlan.id == old_approved_id).first()
        plan_db.refresh(old_plan)
        assert old_plan.status == "superseded"

    def test_approve_invalid_plan_returns_422(self, client, plan_db):
        """A plan with rule violations should be rejected on approval."""
        tomorrow = date.today() + timedelta(days=1)

        # Create a plan with no egg style (violates rules)
        plan_id = _create_draft_plan(
            client, plan_db, plan_date=tomorrow,
            egg_style="invalid_style",  # not a valid egg style
        )

        resp = client.post(f"/api/planner/approve/{plan_id}")
        assert resp.status_code == 422
        assert "rule violations" in resp.json()["detail"].lower()

    def test_approve_valid_plan_with_empty_roti_rejected(self, client, plan_db):
        """A plan without roti count should be rejected."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(
            client, plan_db, plan_date=tomorrow,
            roti_count="",
        )

        resp = client.post(f"/api/planner/approve/{plan_id}")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/planner/swap
# ---------------------------------------------------------------------------

class TestSwapDish:
    def test_swap_dish_in_draft_plan(self, client, plan_db):
        """Should replace a dish in a draft plan when new recipe exists."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        # Create the target recipe in the DB so validation passes
        make_recipe_orm(plan_db, id="avial", name="Avial")

        resp = client.post("/api/planner/swap", json={
            "plan_id": plan_id,
            "old_recipe_id": "sambar",
            "new_recipe_id": "avial",
            "new_recipe_name": "Avial",
            "new_role": "main",
        })
        assert resp.status_code == 200
        data = resp.json()
        dish_ids = [d["recipe_id"] for d in data["dishes"]]
        assert "avial" in dish_ids
        assert "sambar" not in dish_ids

    def test_swap_dish_not_found_in_plan(self, client, plan_db):
        """Swapping a dish that doesn't exist in the plan should 404."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)
        make_recipe_orm(plan_db, id="avial", name="Avial")

        resp = client.post("/api/planner/swap", json={
            "plan_id": plan_id,
            "old_recipe_id": "nonexistent_in_plan",
            "new_recipe_id": "avial",
            "new_recipe_name": "Avial",
            "new_role": "main",
        })
        assert resp.status_code == 404

    def test_swap_with_nonexistent_recipe_returns_404(self, client, plan_db):
        """Swapping to a recipe that doesn't exist in the library should 404."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        resp = client.post("/api/planner/swap", json={
            "plan_id": plan_id,
            "old_recipe_id": "sambar",
            "new_recipe_id": "totally_fake_recipe",
            "new_recipe_name": "Fake",
            "new_role": "main",
        })
        assert resp.status_code == 404
        assert "recipe" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /api/planner/{plan_id}/swap-options
# ---------------------------------------------------------------------------

class TestSwapOptions:
    def test_returns_alternatives_for_main_dish(self, client, plan_db):
        """Should return main recipes that aren't already in the plan."""
        tomorrow = date.today() + timedelta(days=1)
        # Create some recipes
        make_recipe_orm(plan_db, id="sambar", name="Sambar", is_side_dish=False)
        make_recipe_orm(plan_db, id="rasam", name="Rasam", is_side_dish=False)
        make_recipe_orm(plan_db, id="avial", name="Avial", is_side_dish=False)
        make_recipe_orm(plan_db, id="beans_poriyal", name="Beans Poriyal", is_side_dish=True)

        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow, dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            {"recipe_id": "beans_poriyal", "role": "side", "name": "Beans Poriyal"},
        ])

        resp = client.get(f"/api/planner/{plan_id}/swap-options?recipe_id=sambar")
        assert resp.status_code == 200
        data = resp.json()
        # Should return rasam and avial (main dishes not in plan), not beans_poriyal (side)
        ids = [r["id"] for r in data]
        assert "rasam" in ids
        assert "avial" in ids
        assert "sambar" not in ids  # already in plan
        assert "beans_poriyal" not in ids  # side dish, not main

    def test_returns_alternatives_for_side_dish(self, client, plan_db):
        """Should return side recipes that aren't already in the plan."""
        tomorrow = date.today() + timedelta(days=1)
        make_recipe_orm(plan_db, id="sambar", name="Sambar", is_side_dish=False)
        make_recipe_orm(plan_db, id="beans_poriyal", name="Beans Poriyal", is_side_dish=True)
        make_recipe_orm(plan_db, id="thayir_pachadi", name="Thayir Pachadi", is_side_dish=True)

        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow, dishes=[
            {"recipe_id": "sambar", "role": "main", "name": "Sambar"},
            {"recipe_id": "beans_poriyal", "role": "side_dish", "name": "Beans Poriyal"},
        ])

        resp = client.get(f"/api/planner/{plan_id}/swap-options?recipe_id=beans_poriyal")
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data]
        assert "thayir_pachadi" in ids
        assert "beans_poriyal" not in ids  # already in plan
        assert "sambar" not in ids  # main dish, not side

    def test_swap_options_plan_not_found(self, client):
        resp = client.get("/api/planner/99999/swap-options?recipe_id=sambar")
        assert resp.status_code == 404

    def test_swap_options_dish_not_in_plan(self, client, plan_db):
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        resp = client.get(f"/api/planner/{plan_id}/swap-options?recipe_id=nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/planner/{plan_id}/curd-rice
# ---------------------------------------------------------------------------

class TestToggleCurdRice:
    def test_toggle_curd_rice_on(self, client, plan_db):
        """Should set include_curd_rice_side to true."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)

        resp = client.patch(f"/api/planner/{plan_id}/curd-rice", json={"include": True})
        assert resp.status_code == 200
        assert resp.json()["include_curd_rice_side"] is True

    def test_toggle_curd_rice_off(self, client, plan_db):
        """Should set include_curd_rice_side to false."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(
            client, plan_db, plan_date=tomorrow, include_curd_rice_side=True
        )

        resp = client.patch(f"/api/planner/{plan_id}/curd-rice", json={"include": False})
        assert resp.status_code == 200
        assert resp.json()["include_curd_rice_side"] is False

    def test_toggle_curd_rice_only_on_draft(self, client, plan_db):
        """Cannot toggle curd rice on an approved plan."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_approved_plan(client, plan_db, plan_date=tomorrow)

        resp = client.patch(f"/api/planner/{plan_id}/curd-rice", json={"include": True})
        assert resp.status_code == 400

    def test_toggle_curd_rice_plan_not_found(self, client):
        resp = client.patch("/api/planner/99999/curd-rice", json={"include": True})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/meal-history
# ---------------------------------------------------------------------------

class TestMealHistory:
    def test_returns_history_after_approval(self, client, plan_db):
        """After approving a plan, meal history should have an entry."""
        tomorrow = date.today() + timedelta(days=1)
        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)
        client.post(f"/api/planner/approve/{plan_id}")

        resp = client.get("/api/meal-history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["history_date"] == tomorrow.isoformat()

    def test_returns_empty_when_no_history(self, client):
        resp = client.get("/api/meal-history")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Leftover expiry
# ---------------------------------------------------------------------------

class TestLeftoverExpiry:
    def test_stale_leftovers_expired_on_generate(self, client, plan_db):
        """Leftovers older than 2 days should be auto-expired during plan generation."""
        tomorrow = date.today() + timedelta(days=1)

        # Create stale leftover (3 days old)
        stale_lo = Leftover(
            dish_name="Old Dal", servings_estimate="small",
            date_logged=date.today() - timedelta(days=3), status="active"
        )
        # Create fresh leftover (today)
        fresh_lo = Leftover(
            dish_name="Fresh Curry", servings_estimate="1_serving",
            date_logged=date.today(), status="active"
        )
        plan_db.add_all([stale_lo, fresh_lo])
        plan_db.commit()

        mock_plans = [{
            "template_id": "south_indian",
            "cuisine": "South Indian",
            "dishes": [{"recipe_id": "sambar", "role": "main", "name": "Sambar"}],
            "egg_style": "scrambled",
            "roti_count": "standard batch",
            "kid_notes": "",
            "rationale": "Test",
            "missing_ingredients": [],
            "validation": {"is_valid": True, "violations": []},
        }]

        with patch("app.routers.planner.generate_meal_plans", new_callable=AsyncMock, return_value=mock_plans):
            resp = client.post("/api/planner/generate", json={
                "plan_date": tomorrow.isoformat(),
                "vegetables": ["Beans"],
                "use_soon": [],
                "leftovers": [],
            })

        assert resp.status_code == 200

        # Stale leftover should be expired
        plan_db.refresh(stale_lo)
        assert stale_lo.status == "expired"

        # Fresh leftover should remain active
        plan_db.refresh(fresh_lo)
        assert fresh_lo.status == "active"

    def test_stale_leftovers_expired_on_approve(self, client, plan_db):
        """Stale leftovers should be expired when approving a plan."""
        tomorrow = date.today() + timedelta(days=1)

        stale_lo = Leftover(
            dish_name="Very Old Stuff", servings_estimate="small",
            date_logged=date.today() - timedelta(days=5), status="active"
        )
        plan_db.add(stale_lo)
        plan_db.commit()

        plan_id = _create_draft_plan(client, plan_db, plan_date=tomorrow)
        resp = client.post(f"/api/planner/approve/{plan_id}")
        assert resp.status_code == 200

        plan_db.refresh(stale_lo)
        assert stale_lo.status == "expired"
