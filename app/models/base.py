from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[str] = mapped_column(
        default=lambda: datetime.now().isoformat(),
        server_default=func.datetime("now"),
    )
    updated_at: Mapped[str] = mapped_column(
        default=lambda: datetime.now().isoformat(),
        server_default=func.datetime("now"),
        onupdate=lambda: datetime.now().isoformat(),
    )
