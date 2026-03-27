import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Recipe(Base):
    """A house-style recipe — main dish or side dish."""

    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Classification
    cuisine_tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    meal_template: Mapped[str] = mapped_column(String(50), default="")
    is_side_dish: Mapped[bool] = mapped_column(Boolean, default=False)

    # Recipe content
    ingredients: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    steps: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    critical_notes: Mapped[str] = mapped_column(Text, default="")
    kid_adaptation: Mapped[str] = mapped_column(Text, default="")

    # Pairings & metadata
    preferred_side_pairings: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of recipe IDs
    protein_tier: Mapped[str] = mapped_column(String(20), default="medium")  # low / medium / high
    cook_familiarity: Mapped[str] = mapped_column(String(30), default="needs_instructions")  # known / needs_instructions / new

    # Links & media
    links: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    recipe_audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Serving info
    serves: Mapped[str] = mapped_column(String(20), default="3-4")
    prep_time_minutes: Mapped[int | None] = mapped_column(nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # --- JSON helpers ---
    def get_cuisine_tags(self) -> list[str]:
        return json.loads(self.cuisine_tags)

    def set_cuisine_tags(self, tags: list[str]) -> None:
        self.cuisine_tags = json.dumps(tags)

    def get_ingredients(self) -> list[dict]:
        return json.loads(self.ingredients)

    def set_ingredients(self, items: list[dict]) -> None:
        self.ingredients = json.dumps(items)

    def get_steps(self) -> list[dict]:
        return json.loads(self.steps)

    def set_steps(self, items: list[dict]) -> None:
        self.steps = json.dumps(items)

    def get_preferred_side_pairings(self) -> list[str]:
        return json.loads(self.preferred_side_pairings)

    def set_preferred_side_pairings(self, pairings: list[str]) -> None:
        self.preferred_side_pairings = json.dumps(pairings)

    def get_links(self) -> list[str]:
        return json.loads(self.links)

    def set_links(self, links: list[str]) -> None:
        self.links = json.dumps(links)

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id!r}, name={self.name!r})>"
