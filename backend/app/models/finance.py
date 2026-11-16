"""记账：账户 / 分类 / 流水（收入、支出、转账）。"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin

TX_INCOME = "income"
TX_EXPENSE = "expense"
TX_TRANSFER = "transfer"


class Account(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "account"

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), nullable=False, default="bank")
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    icon: Mapped[str | None] = mapped_column(String(32))
    color: Mapped[str | None] = mapped_column(String(16))
    is_archived: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Category(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default=TX_EXPENSE)
    icon: Mapped[str | None] = mapped_column(String(32))
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class Transaction(Base, PkMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "finance_transaction"
    __table_args__ = (
        Index("ix_tx_date_active", "occurred_at", postgresql_where=text("deleted_at IS NULL")),
        Index("ix_tx_account", "account_id"),
    )

    # income / expense / transfer
    tx_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # 支出与收入用 account_id；转账用 account_id(转出) + to_account_id(转入)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False)
    to_account_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("account.id"))

    category_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("category.id"))
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
