"""记账接口：账户、分类、流水与汇总。"""

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import NotFoundError, ValidationError
from app.models.finance import Account, Category, Transaction
from app.schemas.requests import (
    AccountCreate,
    AccountUpdate,
    CategoryCreate,
    TransactionCreate,
)
from app.schemas.serializers import (
    account_out,
    category_out,
    money,
    transaction_out,
)
from app.services import finance as service
from app.services.clock import month_bounds, shift_month, today
from app.services.system_todos import SystemKey, complete_system_todo

router = APIRouter(prefix="/finance", tags=["finance"])


async def _account_names(session) -> dict[int, str]:
    rows = (await session.execute(select(Account.id, Account.name))).all()
    return {row[0]: row[1] for row in rows}


# ---------- 账户 ----------
@router.get("/accounts")
async def list_accounts(session: SessionDep, owner: OwnerDep) -> dict:
    stmt = (
        select(Account)
        .where(Account.deleted_at.is_(None))
        .order_by(Account.sort_order, Account.id)
    )
    accounts = list((await session.execute(stmt)).scalars().all())
    balances = {b["account_id"]: b["balance"] for b in await service.account_balances(session)}
    return {
        "items": [
            {**account_out(a), "balance": money(balances.get(a.id, Decimal("0.00")))}
            for a in accounts
        ]
    }


@router.post("/accounts", status_code=201)
async def create_account(
    payload: AccountCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    account = Account(**payload.model_dump())
    session.add(account)
    await session.flush()
    return account_out(account)


@router.patch("/accounts/{account_id}")
async def update_account(
    account_id: int, payload: AccountUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    account = await session.get(Account, account_id)
    if account is None or account.deleted_at is not None:
        raise NotFoundError("账户不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    await session.flush()
    return account_out(account)


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    account = await session.get(Account, account_id)
    if account is None or account.deleted_at is not None:
        raise NotFoundError("账户不存在")

    used = await session.scalar(
        select(Transaction.id).where(
            Transaction.deleted_at.is_(None),
            (Transaction.account_id == account_id)
            | (Transaction.to_account_id == account_id),
        )
    )
    if used:
        # 有流水的账户只归档，避免历史记录失去引用
        account.is_archived = True
    else:
        account.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True, "archived": bool(used)}


# ---------- 分类 ----------
@router.get("/categories")
async def list_categories(session: SessionDep, owner: OwnerDep) -> dict:
    stmt = (
        select(Category)
        .where(Category.deleted_at.is_(None))
        .order_by(Category.kind, Category.sort_order, Category.id)
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [category_out(c) for c in items]}


@router.post("/categories", status_code=201)
async def create_category(
    payload: CategoryCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    category = Category(**payload.model_dump())
    session.add(category)
    await session.flush()
    return category_out(category)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int, session: SessionDep, owner: OwnerDep
) -> dict:
    category = await session.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise NotFoundError("分类不存在")
    category.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


# ---------- 流水 ----------
@router.get("/transactions")
async def list_transactions(
    session: SessionDep,
    owner: OwnerDep,
    start: date | None = None,
    end: date | None = None,
    account_id: int | None = None,
    category_id: int | None = None,
    limit: int = 200,
) -> dict:
    if start is None or end is None:
        start, end = month_bounds(today())

    stmt = (
        select(Transaction)
        .where(
            Transaction.deleted_at.is_(None),
            Transaction.occurred_on >= start,
            Transaction.occurred_on <= end,
        )
        .order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
        .limit(max(1, min(limit, 200)))
    )
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)

    items = list((await session.execute(stmt)).scalars().all())
    names = await _account_names(session)
    return {"items": [transaction_out(tx, names) for tx in items], "count": len(items)}


@router.post("/transactions", status_code=201)
async def create_transaction(
    payload: TransactionCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    if payload.tx_type == "transfer":
        if payload.to_account_id is None:
            raise ValidationError("转账需要选择转入账户")
        if payload.to_account_id == payload.account_id:
            raise ValidationError("转出与转入账户不能相同")
    elif payload.to_account_id is not None:
        raise ValidationError("仅转账支持转入账户")

    account = await session.get(Account, payload.account_id)
    if account is None or account.deleted_at is not None:
        raise NotFoundError("账户不存在")

    tx = Transaction(**payload.model_dump())
    session.add(tx)
    await session.flush()

    if payload.tx_type in {"income", "expense"}:
        await complete_system_todo(session, SystemKey.FINANCE, payload.occurred_on)

    names = await _account_names(session)
    return transaction_out(tx, names)


@router.delete("/transactions/{tx_id}")
async def delete_transaction(tx_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    tx = await session.get(Transaction, tx_id)
    if tx is None or tx.deleted_at is not None:
        raise NotFoundError("流水不存在")
    tx.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


# ---------- 汇总 ----------
@router.get("/summary")
async def finance_summary(
    session: SessionDep, owner: OwnerDep, year: int | None = None, month: int | None = None
) -> dict:
    base = today()
    target_year = year or base.year
    target_month = month or base.month

    summary = await service.monthly_summary(session, target_year, target_month)
    trend_start = shift_month(date(target_year, target_month, 1), -5)
    trend = await service.monthly_trend(session, trend_start)

    # SQL 只返回有数据的月份；补齐整段窗口，避免「近六月」只剩一根柱子
    trend_by_month = {row["month"]: row for row in trend}
    zero = money(Decimal("0.00"))
    filled_trend: list[dict] = []
    cursor = trend_start
    target_first = date(target_year, target_month, 1)
    while cursor <= target_first:
        key = cursor.strftime("%Y-%m")
        row = trend_by_month.get(key)
        filled_trend.append(
            {
                "month": key,
                "income": row["income"] if row else zero,
                "expense": row["expense"] if row else zero,
            }
        )
        cursor = shift_month(cursor, 1)

    return {
        "year": target_year,
        "month": target_month,
        "month_income": money(summary["income"]),
        "month_expense": money(summary["expense"]),
        "month_net": money(summary["net"]),
        "total_assets": money(summary["total_assets"]),
        "expense_categories": [
            {"name": row["name"], "total": money(row["total"])}
            for row in summary["expense_categories"]
        ],
        "trend": [
            {
                "month": row["month"],
                "income": row["income"],
                "expense": row["expense"],
            }
            for row in filled_trend
        ],
    }
