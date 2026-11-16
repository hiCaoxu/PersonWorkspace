"""娱乐：电影 / 电视剧 / 纪录片 / 播客 / 书籍，看板三态。"""

from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin

ENT_TYPES = ("movie", "tv", "documentary", "podcast", "book")
ENT_STATUSES = ("want", "doing", "done")


class Entertainment(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "entertainment"
    __table_args__ = (
        Index(
            "ix_ent_board",
            "ent_type",
            "status",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    ent_type: Mapped[str] = mapped_column(String(16), nullable=False, default="movie")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="want")

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    year: Mapped[int | None] = mapped_column(SmallInteger)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    progress: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    review: Mapped[str | None] = mapped_column(Text)
    external_url: Mapped[str | None] = mapped_column(String(512))
    is_pinned: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
