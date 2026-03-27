import json
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealPlan(Base):
    """A proposed or approved meal plan for a specific date."""

    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft / approved / completed

    # Template & cuisine
    template_id: Mapped[str] = mapped_column(String(50), default="")
    cuisine: Mapped[str] = mapped_column(String(50), default="")

    # Dishes — JSON list of {recipe_id, role (main/side/accompaniment), name}
    dishes: Mapped[str] = mapped_column(Text, default="[]")

    # Daily constants
    egg_style: Mapped[str] = mapped_column(String(20), default="boiled")
    include_curd_rice_side: Mapped[bool] = mapped_column(Boolean, default=False)
    roti_count: Mapped[str] = mapped_column(String(100), default="")  # e.g. "standard + 5 extra"

    # Generated content
    kid_notes: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    cook_brief_text: Mapped[str] = mapped_column(Text, default="")
    voice_script_text: Mapped[str] = mapped_column(Text, default="")
    voice_audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Shopping list — JSON list of items
    shopping_list: Mapped[str] = mapped_column(Text, default="[]")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # --- JSON helpers ---
    def get_dishes(self) -> list[dict]:
        return json.loads(self.dishes)

    def set_dishes(self, items: list[dict]) -> None:
        self.dishes = json.dumps(items)

    def get_shopping_list(self) -> list[dict]:
        return json.loads(self.shopping_list)

    def set_shopping_list(self, items: list[dict]) -> None:
        self.shopping_list = json.dumps(items)

    def __repr__(self) -> str:
        return f"<MealPlan(id={self.id}, date={self.plan_date}, status={self.status!r})>"
