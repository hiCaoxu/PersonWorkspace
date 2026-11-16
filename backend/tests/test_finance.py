"""记账口径：余额、转账不计收支、汇总与图表数据。"""

from datetime import date
from decimal import Decimal

from app.models.finance import Account, Category, Transaction
from app.services.finance import (
    account_balances,
    category_breakdown,
    month_range,
    monthly_summary,
    monthly_trend,
    period_income_expense,
    total_assets,
)

D = Decimal


async def _setup(db):
    cash = Account(name="现金", account_type="cash", initial_balance=D("1000.00"), sort_order=0)
    bank = Account(name="招商银行", account_type="bank", initial_balance=D("5000.00"), sort_order=1)
    db.add_all([cash, bank])
    await db.flush()

    food = Category(name="餐饮", kind="expense")
    salary = Category(name="工资", kind="income")
    db.add_all([food, salary])
    await db.flush()

    db.add_all(
        [
            Transaction(
                tx_type="income",
                amount=D("8000.00"),
                account_id=bank.id,
                category_id=salary.id,
                occurred_on=date(2026, 11, 1),
            ),
            Transaction(
                tx_type="expense",
                amount=D("35.50"),
                account_id=cash.id,
                category_id=food.id,
                occurred_on=date(2026, 11, 3),
            ),
            Transaction(
                tx_type="expense",
                amount=D("120.00"),
                account_id=bank.id,
                category_id=food.id,
                occurred_on=date(2026, 11, 5),
            ),
            Transaction(
                tx_type="transfer",
                amount=D("500.00"),
                account_id=bank.id,
                to_account_id=cash.id,
                occurred_on=date(2026, 11, 6),
            ),
        ]
    )
    await db.flush()
    return cash, bank


async def test_account_balance_includes_transfer(db):
    cash, bank = await _setup(db)
    balances = {b["account_id"]: b["balance"] for b in await account_balances(db)}
    # 现金：1000 - 35.50 + 500 = 1464.50
    assert balances[cash.id] == D("1464.50")
    # 银行：5000 + 8000 - 120 - 500 = 12380.00
    assert balances[bank.id] == D("12380.00")


async def test_total_assets_equals_sum_of_balances(db):
    await _setup(db)
    assert await total_assets(db) == D("13844.50")


async def test_income_expense_excludes_transfer(db):
    await _setup(db)
    start, end = month_range(2026, 11)
    result = await period_income_expense(db, start, end)
    assert result["income"] == D("8000.00")
    assert result["expense"] == D("155.50")
    assert result["net"] == D("7844.50")


async def test_category_breakdown(db):
    await _setup(db)
    start, end = month_range(2026, 11)
    rows = await category_breakdown(db, start, end, "expense")
    assert rows == [{"name": "餐饮", "total": D("155.50")}]


async def test_monthly_summary_combines_everything(db):
    await _setup(db)
    summary = await monthly_summary(db, 2026, 11)
    assert summary["income"] == D("8000.00")
    assert summary["expense"] == D("155.50")
    assert summary["total_assets"] == D("13844.50")
    assert summary["expense_categories"][0]["name"] == "餐饮"


async def test_monthly_trend_orders_by_month(db):
    cash, _bank = await _setup(db)
    db.add(
        Transaction(
            tx_type="expense",
            amount=D("10.00"),
            account_id=cash.id,
            occurred_on=date(2026, 12, 1),
        )
    )
    await db.flush()
    trend = await monthly_trend(db, date(2026, 1, 1))
    assert [t["month"] for t in trend] == ["2026-11", "2026-12"]


async def test_soft_deleted_transaction_excluded(db):
    from datetime import datetime, timezone

    await _setup(db)
    result = await db.execute(
        Transaction.__table__.select().where(Transaction.amount == D("120.00"))
    )
    tx_id = result.first().id
    tx = await db.get(Transaction, tx_id)
    tx.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    start, end = month_range(2026, 11)
    result2 = await period_income_expense(db, start, end)
    assert result2["expense"] == D("35.50")


async def test_archived_account_excluded_from_assets(db):
    cash, bank = await _setup(db)
    bank.is_archived = True
    await db.flush()
    balances = {b["account_id"]: b["balance"] for b in await account_balances(db)}
    assert cash.id in balances
    assert bank.id not in balances


async def test_month_range_handles_february():
    assert month_range(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))
    assert month_range(2024, 2) == (date(2024, 2, 1), date(2024, 2, 29))
