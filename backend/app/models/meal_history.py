import json
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealHistory(Base):
    """Record of what was actually cooked on a given date."""

    __tablename__ = "meal_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    history_date: Mapped[date] = mapped_column(Date, nullable=False, index=True, unique=True)
    meal_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # What was cooked — JSON list of dish names / recipe IDs
    dishes_cooked: Mapped[str] = mapped_column(Text, default="[]")
    egg_style: Mapped[str] = mapped_column(Text, default="")
    cuisine: Mapped[str] = mapped_column(Text, default="")

    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def get_dishes_cooked(self) -> list[str]:
        return json.loads(self.dishes_cooked)

    def set_dishes_cooked(self, dishes: list[str]) -> None:
        self.dishes_cooked = json.dumps(dishes)

    def __repr__(self) -> str:
        return f"<MealHistory(date={self.history_date}, dishes={self.dishes_cooked})>"
