"""Meal.OS API — household meal operating system."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers.checkin import router as checkin_router
from app.routers.cook_brief import router as cook_brief_router
from app.routers.planner import router as planner_router
from app.routers.planner import history_router
from app.routers.recipes import router as recipes_router
from app.routers.recipes import templates_router
from app.routers.shopping import router as shopping_router
from app.routers.vegetables import router as vegetables_router
from app.routers.voice import router as voice_router
from app.seed.seed_db import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup. Seed data only when AUTO_SEED is enabled."""
    Base.metadata.create_all(bind=engine)
    if settings.AUTO_SEED:
        result = seed_all()
        print(f"[Meal.OS] DB seeded: {result}")
    else:
        print("[Meal.OS] DB tables ready. Run `python -m app.seed.seed_db` to seed data.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI meal operating system for Indian households",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(recipes_router)
app.include_router(templates_router)
app.include_router(vegetables_router)
app.include_router(checkin_router)
app.include_router(planner_router)
app.include_router(history_router)
app.include_router(cook_brief_router)
app.include_router(shopping_router)
app.include_router(voice_router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
