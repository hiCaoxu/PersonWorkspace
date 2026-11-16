"""食物库：《中国食物成分表（第6版）》常用子集 + 用户自定义。"""

from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin

FOOD_CATEGORIES = (
    "谷薯类",
    "肉禽蛋",
    "水产",
    "奶豆",
    "蔬果",
    "坚果",
    "菜肴",
    "饮品",
)


class FoodItem(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "food_item"
    __table_args__ = (
        Index(
            "ix_food_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_food_alias_trgm",
            "alias",
            postgresql_using="gin",
            postgresql_ops={"alias": "gin_trgm_ops"},
        ),
        Index("ix_food_pinyin", "pinyin_abbr"),
        Index("ix_food_category", "category"),
    )

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    alias: Mapped[str | None] = mapped_column(String(200))
    pinyin_abbr: Mapped[str | None] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="菜肴")

    energy_kcal_per_100g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    carb_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(9, 2))

    default_serving_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 1))
    default_serving_label: Mapped[str | None] = mapped_column(String(16))

    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    note: Mapped[str | None] = mapped_column(Text)
