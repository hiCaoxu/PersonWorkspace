"""记账口径：账户余额与收支汇总。

转账不计入收入/支出统计，只在账户间移动资金。
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ZERO = Decimal("0.00")

_BALANCE_SQL = text(
    """
    SELECT a.id AS account_id,
           a.name AS account_name,
           a.account_type AS account_type,
           a.initial_balance
             + COALESCE(SUM(CASE WHEN t.tx_type = 'income' THEN t.amount ELSE 0 END), 0)
             - COALESCE(SUM(CASE WHEN t.tx_type = 'expense' THEN t.amount ELSE 0 END), 0)
             + COALESCE(SUM(CASE WHEN t.tx_type = 'transfer' AND t.to_account_id = a.id
                                 THEN t.amount ELSE 0 END), 0)
             - COALESCE(SUM(CASE WHEN t.tx_type = 'transfer' AND t.account_id = a.id
                                 THEN t.amount ELSE 0 END), 0) AS balance
      FROM account a
      LEFT JOIN finance_transaction t
             ON (t.account_id = a.id OR t.to_account_id = a.id)
            AND t.deleted_at IS NULL
     WHERE a.deleted_at IS NULL
       AND a.is_archived = false
     GROUP BY a.id, a.name, a.initial_balance, a.sort_order
     ORDER BY a.sort_order, a.id
    """
)

_PERIOD_SQL = text(
    """
    SELECT tx_type, COALESCE(SUM(amount), 0) AS total
      FROM finance_transaction
     WHERE deleted_at IS NULL
       AND tx_type IN ('income', 'expense')
       AND occurred_on >= :start
       AND occurred_on <= :end
     GROUP BY tx_type
    """
)

_CATEGORY_SQL = text(
    """
    SELECT COALESCE(c.name, '未分类') AS name,
           COALESCE(SUM(t.amount), 0) AS total
      FROM finance_transaction t
      LEFT JOIN category c ON c.id = t.category_id
     WHERE t.deleted_at IS NULL
       AND t.tx_type = :tx_type
       AND t.occurred_on >= :start
       AND t.occurred_on <= :end
     GROUP BY COALESCE(c.name, '未分类')
     ORDER BY total DESC
    """
)

_TREND_SQL = text(
    """
    SELECT to_char(date_trunc('month', occurred_on), 'YYYY-MM') AS month,
           COALESCE(SUM(CASE WHEN tx_type = 'income' THEN amount END), 0) AS income,
           COALESCE(SUM(CASE WHEN tx_type = 'expense' THEN amount END), 0) AS expense
      FROM finance_transaction
     WHERE deleted_at IS NULL
       AND tx_type IN ('income', 'expense')
       AND occurred_on >= :start
     GROUP BY 1
     ORDER BY 1
    """
)


def month_range(year: int, month: int) -> tuple[date, date]:
    import calendar

    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


async def account_balances(session: AsyncSession) -> list[dict]:
    rows = (await session.execute(_BALANCE_SQL)).mappings().all()
    return [
        {
            "account_id": r["account_id"],
            "account_name": r["account_name"],
            "account_type": r["account_type"],
            "balance": Decimal(r["balance"]).quantize(Decimal("0.01")),
        }
        for r in rows
    ]


async def total_assets(session: AsyncSession) -> Decimal:
    balances = await account_balances(session)
    # 借贷账户是负债，只展示余额，不计入总资产
    return sum(
        (b["balance"] for b in balances if b["account_type"] != "loan"), ZERO
    ).quantize(Decimal("0.01"))


async def period_income_expense(session: AsyncSession, start: date, end: date) -> dict:
    rows = (await session.execute(_PERIOD_SQL, {"start": start, "end": end})).mappings().all()
    data = {"income": ZERO, "expense": ZERO}
    for row in rows:
        data[row["tx_type"]] = Decimal(row["total"]).quantize(Decimal("0.01"))
    data["net"] = (data["income"] - data["expense"]).quantize(Decimal("0.01"))
    return data


async def category_breakdown(
    session: AsyncSession, start: date, end: date, tx_type: str = "expense"
) -> list[dict]:
    rows = (
        await session.execute(_CATEGORY_SQL, {"start": start, "end": end, "tx_type": tx_type})
    ).mappings().all()
    return [
        {"name": r["name"], "total": Decimal(r["total"]).quantize(Decimal("0.01"))} for r in rows
    ]


async def monthly_trend(session: AsyncSession, start: date) -> list[dict]:
    rows = (await session.execute(_TREND_SQL, {"start": start})).mappings().all()
    return [
        {
            "month": r["month"],
            "income": Decimal(r["income"]).quantize(Decimal("0.01")),
            "expense": Decimal(r["expense"]).quantize(Decimal("0.01")),
        }
        for r in rows
    ]


async def monthly_summary(session: AsyncSession, year: int, month: int) -> dict:
    start, end = month_range(year, month)
    period = await period_income_expense(session, start, end)
    return {
        "start": start,
        "end": end,
        **period,
        "total_assets": await total_assets(session),
        "expense_categories": await category_breakdown(session, start, end, "expense"),
    }
