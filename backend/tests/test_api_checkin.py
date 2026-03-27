"""Tests for the Check-in API (Phase 1.1).

Covers:
- POST /api/checkin — submit leftovers + veg availability
- GET /api/checkin/latest — get the most recent check-in
- GET /api/leftovers/active — get currently active leftovers
"""

from datetime import date, timedelta


class TestPostCheckin:
    """POST /api/checkin — submit nightly check-in."""

    def test_checkin_creates_veg_availability_and_leftovers(self, client):
        """A full check-in should store veg availability and leftovers."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "plan_date": tomorrow,
            "leftovers": [
                {"dish_name": "Sambar", "recipe_id": "sambar", "servings_estimate": "small"},
                {"dish_name": "Beans Poriyal", "servings_estimate": "1_serving"},
            ],
            "vegetables": ["French Beans", "Drumstick", "Spinach"],
            "use_soon": ["Spinach"],
        }
        resp = client.post("/api/checkin", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_date"] == tomorrow
        assert data["leftovers_logged"] == 2
        assert data["veg_availability"]["vegetables"] == ["French Beans", "Drumstick", "Spinach"]
        assert data["veg_availability"]["use_soon"] == ["Spinach"]
        assert len(data["active_leftovers"]) == 2

    def test_checkin_no_leftovers(self, client):
        """Check-in with no leftovers should still work."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "plan_date": tomorrow,
            "leftovers": [],
            "vegetables": ["Cabbage"],
            "use_soon": [],
        }
        resp = client.post("/api/checkin", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["leftovers_logged"] == 0
        assert data["veg_availability"]["vegetables"] == ["Cabbage"]

    def test_checkin_no_vegetables(self, client):
        """Check-in with no vegetables should still work."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "plan_date": tomorrow,
            "leftovers": [{"dish_name": "Dal", "servings_estimate": "small"}],
            "vegetables": [],
            "use_soon": [],
        }
        resp = client.post("/api/checkin", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["leftovers_logged"] == 1
        assert data["veg_availability"]["vegetables"] == []

    def test_checkin_updates_existing_veg_availability(self, client):
        """A second check-in for the same date should update veg availability."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # First check-in
        client.post("/api/checkin", json={
            "plan_date": tomorrow,
            "leftovers": [],
            "vegetables": ["Cabbage"],
            "use_soon": [],
        })
        # Second check-in for same date
        resp = client.post("/api/checkin", json={
            "plan_date": tomorrow,
            "leftovers": [],
            "vegetables": ["Drumstick", "Spinach"],
            "use_soon": ["Spinach"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["veg_availability"]["vegetables"] == ["Drumstick", "Spinach"]

    def test_checkin_marks_old_leftovers_consumed_on_resubmit(self, client):
        """Leftover re-submission for same date should discard old active leftovers for that date."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # First check-in with leftovers
        client.post("/api/checkin", json={
            "plan_date": tomorrow,
            "leftovers": [{"dish_name": "Sambar", "servings_estimate": "small"}],
            "vegetables": [],
            "use_soon": [],
        })
        # Second check-in with different leftovers
        resp = client.post("/api/checkin", json={
            "plan_date": tomorrow,
            "leftovers": [{"dish_name": "Dal", "servings_estimate": "1_serving"}],
            "vegetables": [],
            "use_soon": [],
        })
        assert resp.status_code == 200
        data = resp.json()
        # Only the new leftover should be active
        active = [l for l in data["active_leftovers"] if l["status"] == "active"]
        assert len(active) == 1
        assert active[0]["dish_name"] == "Dal"


class TestGetCheckinLatest:
    """GET /api/checkin/latest — get the most recent check-in data."""

    def test_latest_returns_most_recent(self, client):
        """Should return the most recent check-in."""
        day1 = date.today().isoformat()
        day2 = (date.today() + timedelta(days=1)).isoformat()

        client.post("/api/checkin", json={
            "plan_date": day1,
            "leftovers": [],
            "vegetables": ["Cabbage"],
            "use_soon": [],
        })
        client.post("/api/checkin", json={
            "plan_date": day2,
            "leftovers": [{"dish_name": "Dal", "servings_estimate": "small"}],
            "vegetables": ["Spinach"],
            "use_soon": [],
        })

        resp = client.get("/api/checkin/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_date"] == day2
        assert data["vegetables"] == ["Spinach"]

    def test_latest_returns_404_when_none(self, client):
        """Should return 404 if no check-ins exist."""
        resp = client.get("/api/checkin/latest")
        assert resp.status_code == 404


class TestGetActiveLeftovers:
    """GET /api/leftovers/active — get currently active leftovers."""

    def test_returns_active_leftovers(self, client):
        """Should return all active leftovers."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        client.post("/api/checkin", json={
            "plan_date": tomorrow,
            "leftovers": [
                {"dish_name": "Sambar", "servings_estimate": "small"},
                {"dish_name": "Dal", "servings_estimate": "2_plus_servings"},
            ],
            "vegetables": [],
            "use_soon": [],
        })

        resp = client.get("/api/leftovers/active")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = [l["dish_name"] for l in data]
        assert "Sambar" in names
        assert "Dal" in names

    def test_returns_empty_list_when_none(self, client):
        """Should return empty list if no active leftovers."""
        resp = client.get("/api/leftovers/active")
        assert resp.status_code == 200
        assert resp.json() == []
