from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Leftover(Base):
    """Tracks leftover food to inform the next day's plan."""

    __tablename__ = "leftovers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipe_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # small / 1_serving / 2_plus_servings
    servings_estimate: Mapped[str] = mapped_column(String(30), default="small")

    date_logged: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # active / consumed / discarded
    status: Mapped[str] = mapped_column(String(20), default="active")

    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Leftover(dish={self.dish_name!r}, servings={self.servings_estimate!r}, status={self.status!r})>"
