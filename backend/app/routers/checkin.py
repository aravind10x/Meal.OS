"""Check-in API — nightly leftovers + veg availability submission."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.leftover import Leftover
from app.models.veg_availability import VegAvailability
from app.schemas.checkin import (
    CheckinRequest,
    CheckinResponse,
    LeftoverResponse,
    VegAvailabilityResponse,
)

router = APIRouter(prefix="/api", tags=["checkin"])


def _veg_to_response(veg: VegAvailability) -> VegAvailabilityResponse:
    """Convert VegAvailability ORM to response schema."""
    return VegAvailabilityResponse(
        id=veg.id,
        snapshot_date=veg.snapshot_date,
        vegetables=veg.get_vegetables(),
        use_soon=veg.get_use_soon(),
        created_at=veg.created_at,
    )


def _leftover_to_response(lo: Leftover) -> LeftoverResponse:
    """Convert Leftover ORM to response schema."""
    return LeftoverResponse(
        id=lo.id,
        dish_name=lo.dish_name,
        recipe_id=lo.recipe_id,
        servings_estimate=lo.servings_estimate,
        date_logged=lo.date_logged,
        status=lo.status,
        notes=lo.notes,
        created_at=lo.created_at,
    )


@router.post("/checkin", response_model=CheckinResponse)
def submit_checkin(data: CheckinRequest, db: Session = Depends(get_db)):
    """Submit nightly check-in: leftovers + vegetable availability."""
    plan_date = data.plan_date

    # --- Veg Availability: upsert for the date ---
    existing_veg = (
        db.query(VegAvailability)
        .filter(VegAvailability.snapshot_date == plan_date)
        .first()
    )
    if existing_veg:
        existing_veg.set_vegetables(data.vegetables)
        existing_veg.set_use_soon(data.use_soon)
        veg_record = existing_veg
    else:
        veg_record = VegAvailability(snapshot_date=plan_date)
        veg_record.set_vegetables(data.vegetables)
        veg_record.set_use_soon(data.use_soon)
        db.add(veg_record)

    # --- Leftovers: discard old active ones for this date, add new ---
    old_leftovers = (
        db.query(Leftover)
        .filter(Leftover.date_logged == plan_date, Leftover.status == "active")
        .all()
    )
    for lo in old_leftovers:
        lo.status = "discarded"

    new_leftovers = []
    for item in data.leftovers:
        lo = Leftover(
            dish_name=item.dish_name,
            recipe_id=item.recipe_id,
            servings_estimate=item.servings_estimate,
            date_logged=plan_date,
            status="active",
            notes=item.notes,
        )
        db.add(lo)
        new_leftovers.append(lo)

    db.commit()
    db.refresh(veg_record)
    for lo in new_leftovers:
        db.refresh(lo)

    # Fetch all active leftovers (not just today's)
    active_leftovers = (
        db.query(Leftover).filter(Leftover.status == "active").all()
    )

    return CheckinResponse(
        plan_date=plan_date,
        leftovers_logged=len(new_leftovers),
        veg_availability=_veg_to_response(veg_record),
        active_leftovers=[_leftover_to_response(lo) for lo in active_leftovers],
    )


@router.get("/checkin/latest")
def get_latest_checkin(db: Session = Depends(get_db)):
    """Get the most recent check-in data (veg availability + leftovers)."""
    latest_veg = (
        db.query(VegAvailability)
        .order_by(VegAvailability.snapshot_date.desc())
        .first()
    )
    if not latest_veg:
        raise HTTPException(status_code=404, detail="No check-in data found")

    active_leftovers = (
        db.query(Leftover).filter(Leftover.status == "active").all()
    )

    return {
        "plan_date": latest_veg.snapshot_date.isoformat(),
        "vegetables": latest_veg.get_vegetables(),
        "use_soon": latest_veg.get_use_soon(),
        "active_leftovers": [_leftover_to_response(lo) for lo in active_leftovers],
    }


@router.get("/leftovers/active", response_model=list[LeftoverResponse])
def get_active_leftovers(db: Session = Depends(get_db)):
    """Get all currently active leftovers."""
    leftovers = db.query(Leftover).filter(Leftover.status == "active").all()
    return [_leftover_to_response(lo) for lo in leftovers]
