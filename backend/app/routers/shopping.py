"""Shopping list API — delta shopping list from an approved meal plan."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.household import HouseholdProfile
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.veg_availability import VegAvailability
from app.services.shopping import generate_shopping_list

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


class ShoppingItem(BaseModel):
    name: str
    quantity: str
    category: str  # needed / likely_available / pantry_staple
    for_dish: str


class ShoppingListResponse(BaseModel):
    plan_id: int
    items: list[ShoppingItem]


@router.get("/{plan_id}", response_model=ShoppingListResponse)
def get_shopping_list(plan_id: int, db: Session = Depends(get_db)):
    meal_plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found.")

    # Build recipes lookup from the dishes in the plan (safely handle missing keys)
    plan_dishes = meal_plan.get_dishes()
    recipe_ids = [d.get("recipe_id") for d in plan_dishes if d.get("recipe_id")]
    recipes_orm = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all() if recipe_ids else []

    recipes_dict: dict[str, dict] = {}
    for r in recipes_orm:
        recipes_dict[r.id] = {
            "name": r.name,
            "ingredients": r.get_ingredients(),
        }

    # Get available vegetables for the plan date
    veg_snapshot = (
        db.query(VegAvailability)
        .filter(VegAvailability.snapshot_date == meal_plan.plan_date)
        .first()
    )
    available_veg = veg_snapshot.get_vegetables() if veg_snapshot else []

    # Get pantry staples from household profile
    household = db.query(HouseholdProfile).first()
    pantry_staples: list[str] = []
    if household:
        # Pantry staples are stored as list of dicts with "name" key
        for item in household.get_pantry_staples():
            if isinstance(item, dict):
                pantry_staples.append(item.get("name", ""))
            elif isinstance(item, str):
                pantry_staples.append(item)

    plan_dict = {"dishes": plan_dishes}
    items = generate_shopping_list(plan_dict, recipes_dict, available_veg, pantry_staples)

    # Persist the shopping list on the meal plan
    meal_plan.set_shopping_list(items)
    db.commit()

    return ShoppingListResponse(plan_id=plan_id, items=items)
