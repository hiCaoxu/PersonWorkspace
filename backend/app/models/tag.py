"""标签：待办与笔记共用，按 scope 区分作用域。"""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin


class Tag(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tag"
    __table_args__ = (UniqueConstraint("name", "scope", name="uq_tag_name_scope"),)

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="todo")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#B08968")
