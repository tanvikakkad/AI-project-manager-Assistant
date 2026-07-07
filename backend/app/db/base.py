from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Explicit naming convention so every constraint gets a stable, predictable
# name — required for Alembic to generate reliable autogenerate diffs and
# for constraint names to survive across migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in the application."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
