"""Planner API — plan generation, candidates, approval, swap, and history."""

import json
from datetime import date as date_type, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.leftover import Leftover
from app.models.meal_history import MealHistory
from app.models.meal_plan import MealPlan
from app.models.meal_template import MealTemplate
from app.models.recipe import Recipe
from app.models.veg_availability import VegAvailability
from app.models.household import HouseholdProfile
from app.schemas.meal_plan import (
    CurdRiceToggleRequest,
    DishEntry,
    GeneratePlansRequest,
    MealHistoryResponse,
    MealPlanApproveResponse,
    MealPlanResponse,
    SwapDishRequest,
    SwapOptionItem,
    ValidationInfo,
)
from app.services.ai_planner import generate_meal_plans
from app.services.rules_engine import validate_plan

router = APIRouter(prefix="/api/planner", tags=["planner"])
history_router = APIRouter(prefix="/api", tags=["meal-history"])

# Leftovers older than this many days are auto-expired
LEFTOVER_EXPIRY_DAYS = 2


def _plan_to_response(
    plan: MealPlan,
    validation: ValidationInfo | None = None,
) -> MealPlanResponse:
    """Convert MealPlan ORM to response schema."""
    return MealPlanResponse(
        id=plan.id,
        plan_date=plan.plan_date,
        status=plan.status,
        template_id=plan.template_id,
        cuisine=plan.cuisine,
        dishes=[DishEntry(**d) for d in plan.get_dishes()],
        egg_style=plan.egg_style,
        include_curd_rice_side=plan.include_curd_rice_side,
        roti_count=plan.roti_count,
        kid_notes=plan.kid_notes,
        rationale=plan.rationale,
        cook_brief_text=plan.cook_brief_text,
        voice_script_text=plan.voice_script_text,
        voice_audio_url=plan.voice_audio_url,
        shopping_list=plan.get_shopping_list(),
        validation=validation,
        created_at=plan.created_at,
        approved_at=plan.approved_at,
    )


def _expire_stale_leftovers(db: Session) -> int:
    """Auto-expire active leftovers older than LEFTOVER_EXPIRY_DAYS.

    Returns number of leftovers expired.
    """
    cutoff = date_type.today() - timedelta(days=LEFTOVER_EXPIRY_DAYS)
    stale = (
        db.query(Leftover)
        .filter(Leftover.status == "active", Leftover.date_logged < cutoff)
        .all()
    )
    for lo in stale:
        lo.status = "expired"
    if stale:
        db.commit()
    return len(stale)


def _validate_plan_orm(plan: MealPlan, meal_history: list[dict]) -> ValidationInfo:
    """Run rules engine validation on a MealPlan ORM object."""
    plan_dict = {
        "dishes": plan.get_dishes(),
        "egg_style": plan.egg_style,
        "roti_count": plan.roti_count,
        "template_id": plan.template_id,
    }
    result = validate_plan(plan_dict, meal_history=meal_history)
    return ValidationInfo(is_valid=result.is_valid, violations=result.violations)


def _get_meal_history(db: Session, limit: int = 14) -> list[dict]:
    """Get recent meal history as list of dicts for AI planner."""
    entries = (
        db.query(MealHistory)
        .order_by(MealHistory.history_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date": e.history_date.isoformat(),
            "dishes_cooked": e.get_dishes_cooked(),
            "egg_style": e.egg_style,
            "cuisine": e.cuisine,
        }
        for e in entries
    ]


def _get_templates_data(db: Session) -> list[dict]:
    """Get all templates as list of dicts for AI planner."""
    templates = db.query(MealTemplate).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "required_components": t.get_required_components(),
            "optional_components": t.get_optional_components(),
            "carb_rules": t.get_carb_rules(),
            "roti_rules": t.get_roti_rules(),
        }
        for t in templates
    ]


def _get_recipes_data(db: Session) -> list[dict]:
    """Get all recipes as compact dicts for AI planner."""
    recipes = db.query(Recipe).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "cuisine_tags": r.get_cuisine_tags(),
            "meal_template": r.meal_template,
            "is_side_dish": r.is_side_dish,
            "protein_tier": r.protein_tier,
            "cook_familiarity": r.cook_familiarity,
            "preferred_side_pairings": r.get_preferred_side_pairings(),
            "ingredients": r.get_ingredients(),
        }
        for r in recipes
    ]


@router.post("/generate", response_model=list[MealPlanResponse])
async def generate_plans(data: GeneratePlansRequest, db: Session = Depends(get_db)):
    """Generate 2-3 candidate meal plans using AI.

    Stores candidates as draft MealPlans in the database.
    """
    plan_date = data.plan_date

    # Auto-expire stale leftovers before gathering context
    _expire_stale_leftovers(db)

    # Gather context
    templates = _get_templates_data(db)
    recipes = _get_recipes_data(db)
    history = _get_meal_history(db)

    # Get active leftovers
    leftovers = []
    if data.leftovers:
        leftovers = data.leftovers
    else:
        active = db.query(Leftover).filter(Leftover.status == "active").all()
        leftovers = [
            {"dish_name": lo.dish_name, "servings_estimate": lo.servings_estimate}
            for lo in active
        ]

    # Use provided veg data or fetch from DB
    vegetables = data.vegetables
    use_soon = data.use_soon
    if not vegetables:
        veg_record = (
            db.query(VegAvailability)
            .filter(VegAvailability.snapshot_date == plan_date)
            .first()
        )
        if veg_record:
            vegetables = veg_record.get_vegetables()
            use_soon = veg_record.get_use_soon()

    # Call AI planner
    try:
        ai_plans = await generate_meal_plans(
            plan_date=plan_date,
            vegetables=vegetables,
            use_soon=use_soon,
            leftovers=leftovers,
            templates=templates,
            recipes=recipes,
            history=history,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI plan generation failed: {str(e)}")

    # Remove old draft plans for this date
    db.query(MealPlan).filter(
        MealPlan.plan_date == plan_date,
        MealPlan.status == "draft",
    ).delete()
    db.commit()

    # Store candidate plans
    saved_plans = []
    for plan_data in ai_plans:
        plan = MealPlan(
            plan_date=plan_date,
            status="draft",
            template_id=plan_data.get("template_id", ""),
            cuisine=plan_data.get("cuisine", ""),
            egg_style=plan_data.get("egg_style", "boiled"),
            include_curd_rice_side=plan_data.get("include_curd_rice_side", False),
            roti_count=plan_data.get("roti_count", "standard batch"),
            kid_notes=plan_data.get("kid_notes", ""),
            rationale=plan_data.get("rationale", ""),
        )
        plan.set_dishes(plan_data.get("dishes", []))
        # Store missing ingredients in shopping_list temporarily
        missing = plan_data.get("missing_ingredients", [])
        if missing:
            plan.set_shopping_list([{"name": i, "category": "needed"} for i in missing])
        db.add(plan)
        saved_plans.append(plan)

    db.commit()
    for p in saved_plans:
        db.refresh(p)

    return [_plan_to_response(p) for p in saved_plans]


@router.get("/candidates", response_model=list[MealPlanResponse])
def get_candidates(plan_date: str | None = None, db: Session = Depends(get_db)):
    """Get current draft candidate plans.

    Optionally filter by plan_date (ISO format). If not provided,
    returns the most recent batch of draft plans.
    """
    query = db.query(MealPlan).filter(MealPlan.status == "draft")

    if plan_date:
        try:
            parsed_date = date_type.fromisoformat(plan_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        query = query.filter(MealPlan.plan_date == parsed_date)

    plans = query.order_by(MealPlan.created_at.desc()).all()

    # Include validation info for draft plans so UI can show warnings
    history = _get_meal_history(db)
    return [
        _plan_to_response(p, validation=_validate_plan_orm(p, history))
        for p in plans
    ]


@router.get("/approved", response_model=MealPlanResponse | None)
def get_approved_plan(plan_date: str, db: Session = Depends(get_db)):
    """Get the approved plan for a specific date.

    Returns the most recently approved plan for that date, or null if none exists.
    """
    try:
        parsed_date = date_type.fromisoformat(plan_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    plan = (
        db.query(MealPlan)
        .filter(
            MealPlan.plan_date == parsed_date,
            MealPlan.status == "approved",
        )
        .order_by(MealPlan.approved_at.desc())
        .first()
    )

    if not plan:
        return None

    return _plan_to_response(plan)


@router.post("/approve/{plan_id}", response_model=MealPlanApproveResponse)
def approve_plan(plan_id: int, db: Session = Depends(get_db)):
    """Approve a candidate meal plan.

    - Marks the plan as approved
    - Records in meal history
    - Marks leftovers as consumed if they were used
    - Discards other draft plans for the same date
    """
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    if plan.status != "draft":
        raise HTTPException(status_code=400, detail=f"Plan {plan_id} is not in draft status (current: {plan.status})")

    # Re-validate before approval — block if hard constraints are violated
    history = _get_meal_history(db)
    validation = _validate_plan_orm(plan, history)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail=f"Plan has rule violations and cannot be approved: {'; '.join(validation.violations)}",
        )

    # Approve
    plan.status = "approved"
    plan.approved_at = datetime.now(timezone.utc)

    # Supersede any existing approved plans for the same date
    existing_approved = (
        db.query(MealPlan)
        .filter(
            MealPlan.plan_date == plan.plan_date,
            MealPlan.status == "approved",
            MealPlan.id != plan_id,
        )
        .all()
    )
    for old_plan in existing_approved:
        old_plan.status = "superseded"

    # Discard other drafts for the same date
    other_drafts = (
        db.query(MealPlan)
        .filter(
            MealPlan.plan_date == plan.plan_date,
            MealPlan.status == "draft",
            MealPlan.id != plan_id,
        )
        .all()
    )
    for draft in other_drafts:
        draft.status = "discarded"

    # Record in meal history
    dishes = plan.get_dishes()
    dish_ids = [d.get("recipe_id", d.get("name", "")) for d in dishes]

    existing_history = (
        db.query(MealHistory)
        .filter(MealHistory.history_date == plan.plan_date)
        .first()
    )
    if existing_history:
        existing_history.meal_plan_id = plan.id
        existing_history.set_dishes_cooked(dish_ids)
        existing_history.egg_style = plan.egg_style
        existing_history.cuisine = plan.cuisine
        history_recorded = True
    else:
        history_entry = MealHistory(
            history_date=plan.plan_date,
            meal_plan_id=plan.id,
            egg_style=plan.egg_style,
            cuisine=plan.cuisine,
        )
        history_entry.set_dishes_cooked(dish_ids)
        db.add(history_entry)
        history_recorded = True

    # Expire any stale leftovers first
    _expire_stale_leftovers(db)

    # Mark active leftovers for this date as consumed
    active_leftovers = (
        db.query(Leftover)
        .filter(Leftover.date_logged == plan.plan_date, Leftover.status == "active")
        .all()
    )
    for lo in active_leftovers:
        lo.status = "consumed"

    db.commit()
    db.refresh(plan)

    return MealPlanApproveResponse(
        plan=_plan_to_response(plan),
        history_recorded=history_recorded,
    )


@router.post("/swap", response_model=MealPlanResponse)
def swap_dish(data: SwapDishRequest, db: Session = Depends(get_db)):
    """Swap a dish within a draft plan."""
    plan = db.query(MealPlan).filter(MealPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {data.plan_id} not found")
    if plan.status != "draft":
        raise HTTPException(status_code=400, detail="Can only swap dishes in draft plans")

    # Validate the new recipe exists in the database
    new_recipe = db.query(Recipe).filter(Recipe.id == data.new_recipe_id).first()
    if not new_recipe:
        raise HTTPException(
            status_code=404,
            detail=f"Recipe '{data.new_recipe_id}' not found in recipe library",
        )

    dishes = plan.get_dishes()
    found = False
    for i, d in enumerate(dishes):
        if d.get("recipe_id") == data.old_recipe_id:
            dishes[i] = {
                "recipe_id": data.new_recipe_id,
                "role": data.new_role,
                "name": data.new_recipe_name,
            }
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Dish '{data.old_recipe_id}' not found in plan")

    plan.set_dishes(dishes)
    db.commit()
    db.refresh(plan)
    return _plan_to_response(plan)


# Roles that are considered "main" dish roles
_MAIN_ROLES = {"main", "main_curry", "curry"}
_SIDE_ROLES = {"side", "side_dish", "accompaniment"}


@router.get("/{plan_id}/swap-options", response_model=list[SwapOptionItem])
def get_swap_options(
    plan_id: int,
    recipe_id: str,
    db: Session = Depends(get_db),
):
    """Get alternative recipes that can replace a dish in a draft plan.

    Filters by compatible role (main ↔ main, side ↔ side) and excludes
    recipes already present in the plan.
    """
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    dishes = plan.get_dishes()

    # Determine the role of the dish being swapped
    target_dish = next((d for d in dishes if d.get("recipe_id") == recipe_id), None)
    if not target_dish:
        raise HTTPException(
            status_code=404,
            detail=f"Dish '{recipe_id}' not found in plan",
        )

    role = target_dish.get("role", "main")

    # Determine if we want main or side dishes
    want_side = role in _SIDE_ROLES

    # IDs already in the plan — exclude them
    existing_ids = {d.get("recipe_id") for d in dishes}

    # Query compatible recipes
    query = db.query(Recipe).filter(Recipe.is_side_dish == want_side)
    recipes = query.order_by(Recipe.name).all()

    options = []
    for r in recipes:
        if r.id in existing_ids:
            continue
        options.append(
            SwapOptionItem(
                id=r.id,
                name=r.name,
                cuisine_tags=r.get_cuisine_tags(),
                meal_template=r.meal_template,
                is_side_dish=r.is_side_dish,
                protein_tier=r.protein_tier,
                cook_familiarity=r.cook_familiarity,
            )
        )

    return options


@router.patch("/{plan_id}/curd-rice", response_model=MealPlanResponse)
def toggle_curd_rice(
    plan_id: int,
    data: CurdRiceToggleRequest,
    db: Session = Depends(get_db),
):
    """Toggle the optional curd rice side flag on a draft plan."""
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    if plan.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Can only modify draft plans",
        )

    plan.include_curd_rice_side = data.include
    db.commit()
    db.refresh(plan)
    return _plan_to_response(plan)


# --- Meal History endpoint ---

@history_router.get("/meal-history", response_model=list[MealHistoryResponse])
def get_meal_history(limit: int = 14, db: Session = Depends(get_db)):
    """Get recent meal history."""
    entries = (
        db.query(MealHistory)
        .order_by(MealHistory.history_date.desc())
        .limit(limit)
        .all()
    )
    return [
        MealHistoryResponse(
            id=e.id,
            history_date=e.history_date,
            meal_plan_id=e.meal_plan_id,
            dishes_cooked=e.get_dishes_cooked(),
            egg_style=e.egg_style,
            cuisine=e.cuisine,
            notes=e.notes,
            created_at=e.created_at,
        )
        for e in entries
    ]
