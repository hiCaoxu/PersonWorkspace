"""日记：每个自然日唯一一篇。"""

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin


class Diary(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "diary"

    diary_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mood: Mapped[str | None] = mapped_column(String(16))
    weather: Mapped[str | None] = mapped_column(String(16))
