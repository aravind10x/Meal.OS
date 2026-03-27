import json
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VegAvailability(Base):
    """Snapshot of vegetables available for a given date's cooking."""

    __tablename__ = "veg_availability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # JSON list of vegetable names
    vegetables: Mapped[str] = mapped_column(Text, default="[]")

    # JSON list of vegetables to use soon (expiring)
    use_soon: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def get_vegetables(self) -> list[str]:
        return json.loads(self.vegetables)

    def set_vegetables(self, vegs: list[str]) -> None:
        self.vegetables = json.dumps(vegs)

    def get_use_soon(self) -> list[str]:
        return json.loads(self.use_soon)

    def set_use_soon(self, vegs: list[str]) -> None:
        self.use_soon = json.dumps(vegs)

    def __repr__(self) -> str:
        return f"<VegAvailability(date={self.snapshot_date}, count={len(self.get_vegetables())})>"
