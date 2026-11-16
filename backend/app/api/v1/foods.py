"""食物库接口：搜索、常用、自定义食物。"""

from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.food import FoodItem
from app.models.health import HealthDiet
from app.schemas.requests import FoodCreate
from app.schemas.serializers import food_out
from app.services.food import search_foods

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("")
async def list_foods(
    session: SessionDep,
    owner: OwnerDep,
    q: str = "",
    category: str | None = None,
    limit: int = 20,
) -> dict:
    items = await search_foods(session, q=q, category=category, limit=limit)
    return {"items": [food_out(f) for f in items]}


@router.get("/frequent")
async def frequent_foods(session: SessionDep, owner: OwnerDep) -> dict:
    stmt = (
        select(HealthDiet.food_item_id, func.count().label("used"))
        .where(HealthDiet.deleted_at.is_(None), HealthDiet.food_item_id.is_not(None))
        .group_by(HealthDiet.food_item_id)
        .order_by(func.count().desc())
        .limit(10)
    )
    rows = (await session.execute(stmt)).all()
    ids = [row[0] for row in rows]
    if not ids:
        return {"items": []}

    foods = list(
        (await session.execute(select(FoodItem).where(FoodItem.id.in_(ids)))).scalars().all()
    )
    order = {fid: idx for idx, fid in enumerate(ids)}
    foods.sort(key=lambda f: order.get(f.id, 99))
    return {"items": [food_out(f) for f in foods]}


@router.post("", status_code=201)
async def create_food(payload: FoodCreate, session: SessionDep, owner: OwnerDep) -> dict:
    exists = await session.scalar(
        select(FoodItem).where(FoodItem.name == payload.name, FoodItem.deleted_at.is_(None))
    )
    if exists:
        raise ValidationError("该食物已存在，可直接搜索使用")

    name = payload.name.strip()
    if await session.scalar(
        select(FoodItem).where(FoodItem.name == name, FoodItem.deleted_at.is_(None))
    ):
        raise ValidationError("已存在同名食物，请换一个名称或直接搜索使用")

    food = FoodItem(
        name=name,
        alias=payload.alias,
        category=payload.category,
        energy_kcal_per_100g=Decimal(payload.energy_kcal_per_100g),
        default_serving_g=payload.default_serving_g,
        default_serving_label=payload.default_serving_label,
        is_system=False,
    )
    session.add(food)
    await session.flush()
    return food_out(food)


@router.patch("/{food_id}")
async def update_food(
    food_id: int, payload: FoodCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    food = await session.get(FoodItem, food_id)
    if food is None or food.deleted_at is not None:
        raise NotFoundError("食物不存在")
    if food.is_system:
        raise ForbiddenError("系统内置食物不可修改，可另建自定义食物")

    food.name = payload.name.strip()
    food.alias = payload.alias
    food.category = payload.category
    food.energy_kcal_per_100g = Decimal(payload.energy_kcal_per_100g)
    food.default_serving_g = payload.default_serving_g
    food.default_serving_label = payload.default_serving_label
    await session.flush()
    return food_out(food)


@router.delete("/{food_id}")
async def delete_food(food_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    food = await session.get(FoodItem, food_id)
    if food is None or food.deleted_at is not None:
        raise NotFoundError("食物不存在")
    if food.is_system:
        raise ForbiddenError("系统内置食物不可删除")

    from datetime import datetime, timezone

    food.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}
