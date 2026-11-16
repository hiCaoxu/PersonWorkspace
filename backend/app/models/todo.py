"""待办：支持标签、循环规则与每日系统待办。"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin

todo_tag = Table(
    "todo_tag",
    Base.metadata,
    Column("todo_id", BigInteger, ForeignKey("todo.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", BigInteger, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Todo(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "todo"
    __table_args__ = (
        # 每日系统待办幂等的核心保障：同一 system_key + 同一天只能有一条未删除记录
        Index(
            "uq_todo_system_day",
            "system_key",
            "due_date",
            unique=True,
            postgresql_where=text("system_key IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "ix_todo_parent_occurrence",
            "parent_id",
            "occurrence_index",
            unique=True,
            postgresql_where=text("parent_id IS NOT NULL"),
        ),
        Index(
            "ix_todo_due_active",
            "due_date",
            postgresql_where=text("deleted_at IS NULL AND done = false"),
        ),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 系统待办标识：finance / exercise / diet，普通待办为 NULL
    system_key: Mapped[str | None] = mapped_column(String(16))

    # 循环规则
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    interval: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    weekdays: Mapped[str | None] = mapped_column(String(32))
    until: Mapped[date | None] = mapped_column(Date)

    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("todo.id", ondelete="SET NULL"))
    occurrence_index: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary=todo_tag, lazy="selectin", order_by="Tag.id"
    )
