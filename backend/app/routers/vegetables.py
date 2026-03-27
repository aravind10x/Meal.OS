"""Vegetables & Pantry Staples API — reference data for the check-in flow."""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.household import HouseholdProfile

router = APIRouter(prefix="/api", tags=["reference-data"])


@router.get("/vegetables")
def list_vegetables():
    """Return the common vegetables list for the selector UI."""
    vegetables_path = settings.SEED_DIR / "vegetables.json"
    with open(vegetables_path, "r") as f:
        data = json.load(f)
    return data


@router.get("/pantry-staples")
def list_pantry_staples(db: Session = Depends(get_db)):
    """Return pantry staples as a flat list of names.

    Prefers DB household profile, falls back to JSON file (flattened).
    """
    profile = db.query(HouseholdProfile).first()
    if profile:
        return {"pantry_staples": profile.get_pantry_staples()}

    # Fallback: flatten categorized JSON into a flat list to match DB shape
    pantry_path = settings.SEED_DIR / "pantry_staples.json"
    with open(pantry_path, "r") as f:
        data = json.load(f)

    flat_items: list[str] = []
    for category in data.get("pantry_staples", []):
        for item in category.get("items", []):
            flat_items.append(item["name"])
    return {"pantry_staples": flat_items}
