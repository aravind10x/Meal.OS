"""Cook Brief API — generate and retrieve cook briefs for approved plans."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.meal_plan import MealPlan
from app.services.cook_brief import generate_cook_brief
from app.services.plan_context import load_plan_context

router = APIRouter(prefix="/api", tags=["cook-brief"])


@router.get("/brief/{plan_id}")
def get_cook_brief(plan_id: int, db: Session = Depends(get_db)):
    """Generate or retrieve cook brief for a meal plan."""
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    # If brief already generated, return cached version (with voice data if available)
    if plan.cook_brief_text:
        return {
            "plan_id": plan.id,
            "brief_text": plan.cook_brief_text,
            "voice_audio_url": plan.voice_audio_url,
            "voice_script_text": plan.voice_script_text or None,
        }

    # Build shared plan context (includes ingredients, recipe_audio_url)
    plan_dict, recipes_map, leftovers = load_plan_context(plan, db)

    # Generate brief
    brief_text = generate_cook_brief(plan_dict, recipes_map, leftovers=leftovers)

    # Cache it on the plan
    plan.cook_brief_text = brief_text
    db.commit()

    return {
        "plan_id": plan.id,
        "brief_text": brief_text,
        "voice_audio_url": plan.voice_audio_url,
        "voice_script_text": plan.voice_script_text or None,
    }
