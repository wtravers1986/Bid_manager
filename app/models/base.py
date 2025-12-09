"""
Base model mixins and utilities.
"""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declared_attr


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class IDMixin:
    """Mixin that adds an integer primary key id."""

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class UserTrackingMixin:
    """Mixin that tracks which user created/updated a record."""

    @declared_attr
    def created_by(cls):
        return Column(String(255), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(String(255), nullable=True)


def model_to_dict(obj: Any, exclude: list[str] | None = None) -> dict[str, Any]:
    """Convert SQLAlchemy model to dictionary."""
    exclude = exclude or []
    return {
        c.name: getattr(obj, c.name)
        for c in obj.__table__.columns
        if c.name not in exclude
    }
