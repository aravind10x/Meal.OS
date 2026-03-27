"""Alembic migration environment — wired to Meal.OS models and config."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import settings
from app.database import Base

# Import all models so Alembic can detect them for autogenerate
from app.models.recipe import Recipe  # noqa: F401
from app.models.meal_template import MealTemplate  # noqa: F401
from app.models.meal_plan import MealPlan  # noqa: F401
from app.models.meal_history import MealHistory  # noqa: F401
from app.models.leftover import Leftover  # noqa: F401
from app.models.veg_availability import VegAvailability  # noqa: F401
from app.models.shopping_list import ShoppingList  # noqa: F401
from app.models.household import HouseholdProfile  # noqa: F401

# Alembic Config object
config = context.config

# Set the SQLAlchemy URL from our app settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up loggers from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
