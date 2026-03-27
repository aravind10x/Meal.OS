"""Shared test fixtures for Meal.OS backend tests.

Provides:
- An in-memory SQLite database (fresh per test session)
- A FastAPI TestClient wired to the test database
- Factory helpers to create test data without boilerplate
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.recipe import Recipe
from app.models.meal_template import MealTemplate
from app.models.household import HouseholdProfile


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite engine, fresh per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a transactional database session for a test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """FastAPI TestClient that uses the in-memory test database."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_recipe_data(**overrides) -> dict:
    """Return a valid recipe JSON payload for POST /api/recipes.

    Override any field by passing keyword arguments.
    """
    defaults = {
        "id": "test_recipe",
        "name": "Test Recipe",
        "description": "A test recipe for unit tests",
        "cuisine_tags": ["south_indian"],
        "meal_template": "south_indian",
        "is_side_dish": False,
        "ingredients": [
            {"name": "Tomato", "quantity": "2", "category": "vegetable"},
            {"name": "Salt", "quantity": "to taste", "category": "pantry"},
        ],
        "steps": [
            {"order": 1, "instruction": "Chop tomatoes", "is_critical": False},
            {"order": 2, "instruction": "Cook with spices", "is_critical": True},
        ],
        "critical_notes": "Use fresh tomatoes",
        "kid_adaptation": "Reduce spice",
        "preferred_side_pairings": ["beans_poriyal"],
        "protein_tier": "medium",
        "cook_familiarity": "needs_instructions",
        "links": [],
        "serves": "3-4",
        "prep_time_minutes": 10,
        "cook_time_minutes": 30,
    }
    defaults.update(overrides)
    return defaults


def make_recipe_orm(db_session, **overrides) -> Recipe:
    """Create and persist a Recipe ORM object in the test database."""
    data = make_recipe_data(**overrides)
    recipe = Recipe(
        id=data["id"],
        name=data["name"],
        description=data.get("description", ""),
        cuisine_tags=json.dumps(data.get("cuisine_tags", [])),
        meal_template=data.get("meal_template", ""),
        is_side_dish=data.get("is_side_dish", False),
        ingredients=json.dumps(data.get("ingredients", [])),
        steps=json.dumps(data.get("steps", [])),
        critical_notes=data.get("critical_notes", ""),
        kid_adaptation=data.get("kid_adaptation", ""),
        preferred_side_pairings=json.dumps(data.get("preferred_side_pairings", [])),
        protein_tier=data.get("protein_tier", "medium"),
        cook_familiarity=data.get("cook_familiarity", "needs_instructions"),
        links=json.dumps(data.get("links", [])),
        serves=data.get("serves", "3-4"),
        prep_time_minutes=data.get("prep_time_minutes"),
        cook_time_minutes=data.get("cook_time_minutes"),
    )
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)
    return recipe


def make_template_orm(db_session, **overrides) -> MealTemplate:
    """Create and persist a MealTemplate ORM object in the test database."""
    defaults = {
        "id": "test_template",
        "name": "Test Template",
        "description": "A test template",
        "required_components": [{"role": "main_curry", "description": "Main curry"}],
        "optional_components": [{"role": "side", "description": "Optional side"}],
        "carb_rules": {"default": "rice"},
        "roti_rules": {"shweta": "always"},
    }
    defaults.update(overrides)

    tmpl = MealTemplate(
        id=defaults["id"],
        name=defaults["name"],
        description=defaults.get("description", ""),
        required_components=json.dumps(defaults.get("required_components", [])),
        optional_components=json.dumps(defaults.get("optional_components", [])),
        carb_rules=json.dumps(defaults.get("carb_rules", {})),
        roti_rules=json.dumps(defaults.get("roti_rules", {})),
    )
    db_session.add(tmpl)
    db_session.commit()
    db_session.refresh(tmpl)
    return tmpl


def make_household_orm(db_session, **overrides) -> HouseholdProfile:
    """Create and persist a HouseholdProfile ORM object in the test database."""
    defaults = {
        "family_name": "Test Family",
        "members": [{"name": "Test User", "role": "adult"}],
        "cook_info": {"name": "Test Cook", "languages": ["hindi"]},
        "rules": {"roti_daily": True, "eggs_daily": 5},
        "kid_general_rules": ["Less spicy"],
        "pantry_staples": ["salt", "oil", "rice"],
    }
    defaults.update(overrides)

    profile = HouseholdProfile(
        family_name=defaults["family_name"],
        members=json.dumps(defaults.get("members", [])),
        cook_info=json.dumps(defaults.get("cook_info", {})),
        rules=json.dumps(defaults.get("rules", {})),
        kid_general_rules=json.dumps(defaults.get("kid_general_rules", [])),
        pantry_staples=json.dumps(defaults.get("pantry_staples", [])),
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile
