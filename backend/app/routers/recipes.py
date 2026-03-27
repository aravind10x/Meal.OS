"""Recipe Library API — CRUD operations for house-style recipes."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recipe import Recipe
from app.models.meal_template import MealTemplate
from app.schemas.recipe import (
    CuisineTag,
    MealTemplateName,
    RecipeCreate,
    RecipeListItem,
    RecipeResponse,
    RecipeUpdate,
    MealTemplateResponse,
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _recipe_to_response(recipe: Recipe) -> RecipeResponse:
    """Convert a Recipe ORM object to a RecipeResponse with parsed JSON fields."""
    return RecipeResponse(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        cuisine_tags=recipe.get_cuisine_tags(),
        meal_template=recipe.meal_template,
        is_side_dish=recipe.is_side_dish,
        ingredients=recipe.get_ingredients(),
        steps=recipe.get_steps(),
        critical_notes=recipe.critical_notes,
        kid_adaptation=recipe.kid_adaptation,
        preferred_side_pairings=recipe.get_preferred_side_pairings(),
        protein_tier=recipe.protein_tier,
        cook_familiarity=recipe.cook_familiarity,
        links=recipe.get_links(),
        recipe_audio_url=recipe.recipe_audio_url,
        serves=recipe.serves,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


def _recipe_to_list_item(recipe: Recipe) -> RecipeListItem:
    """Convert a Recipe ORM object to a lightweight list item."""
    return RecipeListItem(
        id=recipe.id,
        name=recipe.name,
        cuisine_tags=recipe.get_cuisine_tags(),
        meal_template=recipe.meal_template,
        is_side_dish=recipe.is_side_dish,
        protein_tier=recipe.protein_tier,
        cook_familiarity=recipe.cook_familiarity,
        serves=recipe.serves,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
    )


@router.get("", response_model=list[RecipeListItem])
def list_recipes(
    cuisine: str | None = Query(None, description="Filter by cuisine tag"),
    template: str | None = Query(None, description="Filter by meal template"),
    side_only: bool | None = Query(None, description="Filter side dishes only"),
    db: Session = Depends(get_db),
):
    """List all recipes with optional filtering."""
    query = db.query(Recipe)

    if side_only is True:
        query = query.filter(Recipe.is_side_dish == True)
    elif side_only is False:
        query = query.filter(Recipe.is_side_dish == False)

    recipes = query.order_by(Recipe.name).all()

    # Apply in-memory filters for JSON fields
    results = []
    for recipe in recipes:
        if cuisine and cuisine not in recipe.get_cuisine_tags():
            continue
        if template and recipe.meal_template != template:
            continue
        results.append(_recipe_to_list_item(recipe))

    return results


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get a recipe by ID with full details."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")
    return _recipe_to_response(recipe)


@router.post("", response_model=RecipeResponse, status_code=201)
def create_recipe(data: RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe."""
    existing = db.query(Recipe).filter(Recipe.id == data.id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Recipe '{data.id}' already exists")

    recipe = Recipe(
        id=data.id,
        name=data.name,
        description=data.description,
        cuisine_tags=json.dumps(data.cuisine_tags),
        meal_template=data.meal_template,
        is_side_dish=data.is_side_dish,
        ingredients=json.dumps([ing.model_dump() for ing in data.ingredients]),
        steps=json.dumps([step.model_dump() for step in data.steps]),
        critical_notes=data.critical_notes,
        kid_adaptation=data.kid_adaptation,
        preferred_side_pairings=json.dumps(data.preferred_side_pairings),
        protein_tier=data.protein_tier,
        cook_familiarity=data.cook_familiarity,
        links=json.dumps(data.links),
        recipe_audio_url=data.recipe_audio_url,
        serves=data.serves,
        prep_time_minutes=data.prep_time_minutes,
        cook_time_minutes=data.cook_time_minutes,
    )
    db.add(recipe)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Recipe '{data.id}' already exists")
    db.refresh(recipe)
    return _recipe_to_response(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: str, data: RecipeUpdate, db: Session = Depends(get_db)):
    """Update an existing recipe (partial update)."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle JSON fields specially
    json_list_fields = {
        "cuisine_tags": recipe.set_cuisine_tags,
        "preferred_side_pairings": recipe.set_preferred_side_pairings,
        "links": recipe.set_links,
    }
    for field, setter in json_list_fields.items():
        if field in update_data:
            setter(update_data.pop(field))

    if "ingredients" in update_data:
        recipe.set_ingredients([ing.model_dump() if hasattr(ing, 'model_dump') else ing for ing in update_data.pop("ingredients")])

    if "steps" in update_data:
        recipe.set_steps([step.model_dump() if hasattr(step, 'model_dump') else step for step in update_data.pop("steps")])

    # Set remaining simple fields
    for field, value in update_data.items():
        setattr(recipe, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Update would violate a uniqueness constraint")
    db.refresh(recipe)
    return _recipe_to_response(recipe)


@router.patch("/{recipe_id}/familiarity")
def update_recipe_familiarity(recipe_id: str, data: dict, db: Session = Depends(get_db)):
    """Update cook_familiarity for a recipe (quick toggle)."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")

    new_familiarity = data.get("cook_familiarity", "")
    valid_values = {"known", "needs_instructions", "new"}
    if new_familiarity not in valid_values:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid cook_familiarity value. Must be one of: {valid_values}",
        )

    recipe.cook_familiarity = new_familiarity
    db.commit()
    db.refresh(recipe)

    return {
        "id": recipe.id,
        "name": recipe.name,
        "cook_familiarity": recipe.cook_familiarity,
    }


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Delete a recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found")

    db.delete(recipe)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cannot delete: recipe is referenced by other data")


# --- Meal Templates ---

templates_router = APIRouter(prefix="/api/templates", tags=["templates"])


@templates_router.get("", response_model=list[MealTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    """List all meal templates."""
    templates = db.query(MealTemplate).order_by(MealTemplate.name).all()
    results = []
    for tmpl in templates:
        results.append(MealTemplateResponse(
            id=tmpl.id,
            name=tmpl.name,
            description=tmpl.description,
            required_components=tmpl.get_required_components(),
            optional_components=tmpl.get_optional_components(),
            carb_rules=tmpl.get_carb_rules(),
            roti_rules=tmpl.get_roti_rules(),
        ))
    return results
