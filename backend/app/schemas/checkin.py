"""Schemas for the nightly check-in flow."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# --- Leftovers ---

ServingsEstimate = Literal["small", "1_serving", "2_plus_servings"]


class LeftoverItem(BaseModel):
    """A single leftover entry from the check-in."""
    dish_name: str = Field(..., min_length=1)
    recipe_id: str | None = None
    servings_estimate: ServingsEstimate = "small"
    notes: str = ""


class LeftoverResponse(BaseModel):
    """Response for an active leftover."""
    id: int
    dish_name: str
    recipe_id: str | None = None
    servings_estimate: str
    date_logged: date
    status: str
    notes: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Vegetable Availability ---

class VegAvailabilityData(BaseModel):
    """Vegetables available for tomorrow's cooking."""
    vegetables: list[str] = Field(default_factory=list)
    use_soon: list[str] = Field(default_factory=list)


class VegAvailabilityResponse(BaseModel):
    """Response for a veg availability snapshot."""
    id: int
    snapshot_date: date
    vegetables: list[str] = Field(default_factory=list)
    use_soon: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Check-in (combined) ---

class CheckinRequest(BaseModel):
    """Nightly check-in: leftovers + veg availability for tomorrow."""
    plan_date: date = Field(..., description="The date being planned for (tomorrow)")
    leftovers: list[LeftoverItem] = Field(default_factory=list)
    vegetables: list[str] = Field(default_factory=list)
    use_soon: list[str] = Field(default_factory=list)


class CheckinResponse(BaseModel):
    """Response after completing check-in."""
    plan_date: date
    leftovers_logged: int
    veg_availability: VegAvailabilityResponse
    active_leftovers: list[LeftoverResponse]
