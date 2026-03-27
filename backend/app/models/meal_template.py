import json

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MealTemplate(Base):
    """A cuisine-specific meal template defining the structure of a complete meal."""

    __tablename__ = "meal_templates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # Components — stored as JSON
    required_components: Mapped[str] = mapped_column(Text, default="[]")
    optional_components: Mapped[str] = mapped_column(Text, default="[]")

    # Rules — stored as JSON
    carb_rules: Mapped[str] = mapped_column(Text, default="{}")
    roti_rules: Mapped[str] = mapped_column(Text, default="{}")

    # --- JSON helpers ---
    def get_required_components(self) -> list[dict]:
        return json.loads(self.required_components)

    def set_required_components(self, items: list[dict]) -> None:
        self.required_components = json.dumps(items)

    def get_optional_components(self) -> list[dict]:
        return json.loads(self.optional_components)

    def set_optional_components(self, items: list[dict]) -> None:
        self.optional_components = json.dumps(items)

    def get_carb_rules(self) -> dict:
        return json.loads(self.carb_rules)

    def get_roti_rules(self) -> dict:
        return json.loads(self.roti_rules)

    def __repr__(self) -> str:
        return f"<MealTemplate(id={self.id!r}, name={self.name!r})>"
