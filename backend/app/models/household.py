import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HouseholdProfile(Base):
    """Household configuration — rules, preferences, and member details."""

    __tablename__ = "household_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    family_name: Mapped[str] = mapped_column(String(200), default="")

    # All stored as JSON for flexibility
    members: Mapped[str] = mapped_column(Text, default="[]")
    cook_info: Mapped[str] = mapped_column(Text, default="{}")
    rules: Mapped[str] = mapped_column(Text, default="{}")
    kid_general_rules: Mapped[str] = mapped_column(Text, default="[]")
    pantry_staples: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # --- JSON helpers ---
    def get_members(self) -> list[dict]:
        return json.loads(self.members)

    def get_cook_info(self) -> dict:
        return json.loads(self.cook_info)

    def get_rules(self) -> dict:
        return json.loads(self.rules)

    def get_kid_general_rules(self) -> list[str]:
        return json.loads(self.kid_general_rules)

    def get_pantry_staples(self) -> list[dict]:
        return json.loads(self.pantry_staples)

    def __repr__(self) -> str:
        return f"<HouseholdProfile(id={self.id}, family={self.family_name!r})>"
