"""健康：锻炼 / 饮食 / 体重 / 睡眠。"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin


class HealthExercise(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "health_exercise"
    __table_args__ = (Index("ix_exercise_date", "record_date", postgresql_where=text("deleted_at IS NULL")),)

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(7, 1))
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    intensity: Mapped[str | None] = mapped_column(String(16))
    note: Mapped[str | None] = mapped_column(Text)


class HealthDiet(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "health_diet"
    __table_args__ = (Index("ix_diet_date", "record_date", postgresql_where=text("deleted_at IS NULL")),)

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal: Mapped[str] = mapped_column(String(16), nullable=False, default="lunch")

    # 关联食物库，允许为空（纯手动录入）
    food_item_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("food_item.id", ondelete="SET NULL"))
    # 名称快照：食物被删除后历史记录仍可读
    food_name: Mapped[str] = mapped_column(String(64), nullable=False)

    quantity_g: Mapped[Decimal] = mapped_column(Numeric(7, 1), nullable=False, default=Decimal("100.0"))
    # 热量快照，可被用户手动覆盖；统计只聚合此列
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(7, 1), nullable=False)
    calories_manual: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    carb_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    note: Mapped[str | None] = mapped_column(Text)


class HealthWeight(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "health_weight"
    __table_args__ = (Index("ix_weight_date", "record_date", postgresql_where=text("deleted_at IS NULL")),)

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    body_fat_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    note: Mapped[str | None] = mapped_column(Text)


class HealthSleep(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "health_sleep"
    __table_args__ = (Index("ix_sleep_date", "record_date", postgresql_where=text("deleted_at IS NULL")),)

    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_at: Mapped[datetime | None] = mapped_column()
    wake_at: Mapped[datetime | None] = mapped_column()
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality: Mapped[int | None] = mapped_column(SmallInteger)
    note: Mapped[str | None] = mapped_column(Text)
