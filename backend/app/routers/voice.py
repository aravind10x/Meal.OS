"""Voice Script & Audio API — generate Hindi voice scripts and TTS audio."""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.services.plan_context import load_plan_context
from app.services.voice_script import generate_voice_script
from app.services.tts import synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voice"])


# ---------------------------------------------------------------------------
# Voice Script endpoint
# ---------------------------------------------------------------------------


@router.get("/voice-script/{plan_id}")
async def get_voice_script(plan_id: int, db: Session = Depends(get_db)):
    """Generate or retrieve Hindi voice script for an approved meal plan.

    Returns cached script if available; otherwise generates via LLM and caches.
    """
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    if plan.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Voice script can only be generated for approved plans",
        )

    # Return cached if available
    if plan.voice_script_text:
        return {"plan_id": plan.id, "script_text": plan.voice_script_text}

    # Generate via LLM
    plan_dict, recipes_map, leftovers = load_plan_context(plan, db)

    try:
        script_text = await generate_voice_script(
            plan_dict, recipes_map, leftovers=leftovers
        )
    except Exception as e:
        logger.error(f"Voice script generation failed for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=502, detail="Voice script generation failed. Please try again."
        )

    # Cache on model
    plan.voice_script_text = script_text
    db.commit()

    return {"plan_id": plan.id, "script_text": script_text}


# ---------------------------------------------------------------------------
# Voice Audio (TTS) endpoint
# ---------------------------------------------------------------------------


@router.get("/voice-audio/{plan_id}")
async def get_voice_audio(plan_id: int, db: Session = Depends(get_db)):
    """Generate or retrieve TTS audio for an approved meal plan.

    Generates voice script first if needed, then synthesizes audio.
    Returns audio file URL (or script text as fallback if TTS fails).
    """
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    if plan.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Voice audio can only be generated for approved plans",
        )

    # If audio already exists, return it
    if plan.voice_audio_url:
        return {
            "plan_id": plan.id,
            "audio_url": plan.voice_audio_url,
            "script_text": plan.voice_script_text,
        }

    # Ensure we have a voice script
    if not plan.voice_script_text:
        plan_dict, recipes_map, leftovers = load_plan_context(plan, db)
        try:
            script_text = await generate_voice_script(
                plan_dict, recipes_map, leftovers=leftovers
            )
            plan.voice_script_text = script_text
            db.commit()
        except Exception as e:
            logger.error(f"Voice script generation failed for plan {plan_id}: {e}")
            raise HTTPException(
                status_code=502,
                detail="Voice script generation failed. Please try again.",
            )

    # Synthesize audio via TTS
    try:
        audio_filename = f"brief_{plan_id}.mp3"
        audio_path = await synthesize_speech(
            plan.voice_script_text, audio_filename
        )
        audio_url = f"/api/audio/{audio_filename}"
        plan.voice_audio_url = audio_url
        db.commit()

        return {
            "plan_id": plan.id,
            "audio_url": audio_url,
            "script_text": plan.voice_script_text,
        }
    except Exception as e:
        logger.error(f"TTS synthesis failed for plan {plan_id}: {e}")
        # Graceful fallback: return script text so user can read/record manually
        return {
            "plan_id": plan.id,
            "audio_url": None,
            "script_text": plan.voice_script_text,
            "tts_error": "Audio generation failed. You can read the script below or record manually.",
        }


# ---------------------------------------------------------------------------
# Static audio file serving
# ---------------------------------------------------------------------------


@router.get("/audio/{filename:path}")
async def serve_audio(filename: str):
    """Serve an audio file from the audio directory.

    Supports nested paths like recipes/sambar.mp3.
    """
    # Sanitize to prevent directory traversal — resolve and ensure strictly within AUDIO_DIR
    audio_dir = settings.AUDIO_DIR.resolve()
    audio_path = (audio_dir / filename).resolve()

    # Use Path.is_relative_to() for strict containment check (not bypassable by sibling prefixes)
    if not audio_path.is_relative_to(audio_dir):
        raise HTTPException(status_code=404, detail="Audio file not found")

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=audio_path.name,
    )


# ---------------------------------------------------------------------------
# Pre-recorded recipe audio
# ---------------------------------------------------------------------------


@router.post("/recipes/{recipe_id}/audio")
async def upload_recipe_audio(
    recipe_id: str,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a pre-recorded audio file for a recipe.

    Stores the file in audio_files/recipes/ and updates recipe_audio_url.
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")

    # Ensure recipes audio directory exists
    recipes_audio_dir = settings.AUDIO_DIR / "recipes"
    recipes_audio_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension
    ext = Path(audio_file.filename or "audio.mp3").suffix or ".mp3"
    safe_filename = f"{recipe_id}{ext}"
    file_path = recipes_audio_dir / safe_filename

    # Save the uploaded file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)

    # Update recipe
    audio_url = f"/api/audio/recipes/{safe_filename}"
    recipe.recipe_audio_url = audio_url
    db.commit()

    return {
        "recipe_id": recipe_id,
        "audio_url": audio_url,
        "filename": safe_filename,
    }


@router.get("/recipes/{recipe_id}/audio")
async def get_recipe_audio(recipe_id: str, db: Session = Depends(get_db)):
    """Serve the pre-recorded audio file for a recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")

    if not recipe.recipe_audio_url:
        raise HTTPException(
            status_code=404,
            detail=f"No pre-recorded audio for recipe '{recipe_id}'",
        )

    # Extract filename from URL and serve
    # URL format: /api/audio/recipes/{filename}
    url_parts = recipe.recipe_audio_url.split("/")
    filename = url_parts[-1] if url_parts else ""
    audio_path = settings.AUDIO_DIR / "recipes" / filename

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename,
    )
