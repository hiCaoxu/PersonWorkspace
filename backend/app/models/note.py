"""笔记：Markdown 正文 + 标签。"""

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Index, String, Table, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin

note_tag = Table(
    "note_tag",
    Base.metadata,
    Column("note_id", BigInteger, ForeignKey("note.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", BigInteger, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Note(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "note"
    __table_args__ = (
        Index("ix_note_updated", "updated_at", postgresql_where=text("deleted_at IS NULL")),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False, default="无标题")
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary=note_tag, lazy="selectin", order_by="Tag.id"
    )
