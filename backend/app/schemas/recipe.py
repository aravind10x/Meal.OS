from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Domain-constrained types
CuisineTag = Literal["south_indian", "north_indian", "indo_chinese", "bengali", "comfort", "international"]
ProteinTier = Literal["low", "medium", "high"]
CookFamiliarity = Literal["known", "needs_instructions", "new"]
IngredientCategory = Literal["pantry", "vegetable"]
MealTemplateName = Literal["south_indian", "north_indian", "indo_chinese", "bengali", "comfort", "international", ""]


class IngredientItem(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: str = ""
    category: IngredientCategory = "pantry"
    note: str = ""
    flexible_with: list[str] = Field(default_factory=list)


class StepItem(BaseModel):
    order: int = Field(..., ge=1)
    instruction: str = Field(..., min_length=1)
    is_critical: bool = False


class RecipeBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    cuisine_tags: list[CuisineTag] = Field(default_factory=list)
    meal_template: MealTemplateName = ""
    is_side_dish: bool = False
    ingredients: list[IngredientItem] = Field(default_factory=list)
    steps: list[StepItem] = Field(default_factory=list)
    critical_notes: str = ""
    kid_adaptation: str = ""
    preferred_side_pairings: list[str] = Field(default_factory=list)
    protein_tier: ProteinTier = "medium"
    cook_familiarity: CookFamiliarity = "needs_instructions"
    links: list[str] = Field(default_factory=list)
    recipe_audio_url: str | None = None
    serves: str = "3-4"
    prep_time_minutes: int | None = Field(None, ge=0)
    cook_time_minutes: int | None = Field(None, ge=0)


class RecipeCreate(RecipeBase):
    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique slug ID for the recipe, e.g. 'sambar'",
    )


class RecipeUpdate(BaseModel):
    """All fields optional for partial updates."""
    name: str | None = Field(None, min_length=1)
    description: str | None = None
    cuisine_tags: list[CuisineTag] | None = None
    meal_template: MealTemplateName | None = None
    is_side_dish: bool | None = None
    ingredients: list[IngredientItem] | None = None
    steps: list[StepItem] | None = None
    critical_notes: str | None = None
    kid_adaptation: str | None = None
    preferred_side_pairings: list[str] | None = None
    protein_tier: ProteinTier | None = None
    cook_familiarity: CookFamiliarity | None = None
    links: list[str] | None = None
    recipe_audio_url: str | None = None
    serves: str | None = None
    prep_time_minutes: int | None = Field(None, ge=0)
    cook_time_minutes: int | None = Field(None, ge=0)


class RecipeResponse(RecipeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipeListItem(BaseModel):
    """Lightweight recipe item for list views."""
    id: str
    name: str
    cuisine_tags: list[str] = Field(default_factory=list)
    meal_template: str = ""
    is_side_dish: bool = False
    protein_tier: str = "medium"
    cook_familiarity: str = "needs_instructions"
    serves: str = "3-4"
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None

    model_config = {"from_attributes": True}


class MealTemplateResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    required_components: list[dict] = Field(default_factory=list)
    optional_components: list[dict] = Field(default_factory=list)
    carb_rules: dict = Field(default_factory=dict)
    roti_rules: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}
