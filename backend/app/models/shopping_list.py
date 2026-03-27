import json
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ShoppingList(Base):
    """Delta shopping list generated from an approved meal plan."""

    __tablename__ = "shopping_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # JSON list of {name, quantity, category (needed/likely_available/pantry_staple), for_dish}
    items: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def get_items(self) -> list[dict]:
        return json.loads(self.items)

    def set_items(self, items: list[dict]) -> None:
        self.items = json.dumps(items)

    def __repr__(self) -> str:
        return f"<ShoppingList(date={self.list_date}, items={len(self.get_items())})>"
