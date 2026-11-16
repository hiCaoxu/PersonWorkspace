"""档案：个人信息（单行）与人生大事。"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Index, Numeric, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin


class Profile(Base, PkMixin, TimestampMixin):
    """单行表：id 固定为 1。身份证仅存密文与脱敏串。"""

    __tablename__ = "profile"

    name: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    id_card_ciphertext: Mapped[str | None] = mapped_column(Text)
    id_card_masked: Mapped[str | None] = mapped_column(String(32))
    # 证件登记生日（公历，来自身份证号）
    id_card_birthday: Mapped[date | None] = mapped_column(Date)
    # 真实生日（农历）
    lunar_birthday_year: Mapped[int | None] = mapped_column(SmallInteger)
    lunar_birthday_month: Mapped[int | None] = mapped_column(SmallInteger)
    lunar_birthday_day: Mapped[int | None] = mapped_column(SmallInteger)
    # 换算出的公历生日
    solar_birthday: Mapped[date | None] = mapped_column(Date)

    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))
    wechat: Mapped[str | None] = mapped_column(String(64))
    blood_type: Mapped[str | None] = mapped_column(String(8))
    address: Mapped[str | None] = mapped_column(String(256))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    bio: Mapped[str | None] = mapped_column(Text)


class LifeEvent(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "life_event"
    __table_args__ = (Index("ix_life_event_date", "event_date", postgresql_where=text("deleted_at IS NULL")),)

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(16), nullable=False, default="other")
    location: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(512))
    is_highlight: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
