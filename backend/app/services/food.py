"""食物热量折算与搜索。

热量口径唯一来源：kcal = 每100g能量 × 摄入克数 / 100，四舍五入到 0.1。
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodItem

KCAL_STEP = Decimal("0.1")
MAX_QUANTITY_G = Decimal("5000")
DEFAULT_SEARCH_LIMIT = 20


class FoodError(ValueError):
    pass


def _to_decimal(value: Decimal | int | float | str, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise FoodError(f"{field} 不是合法数字: {value}") from exc
    if not result.is_finite():
        raise FoodError(f"{field} 不是有限数值")
    return result


def compute_kcal(energy_per_100g: Decimal | int | float | str, quantity_g: Decimal | int | float | str) -> Decimal:
    """116 kcal/100g × 150g -> 174.0"""
    per = _to_decimal(energy_per_100g, "每100g能量")
    qty = _to_decimal(quantity_g, "摄入克数")
    if per < 0:
        raise FoodError("每100g能量不能为负")
    if qty <= 0:
        raise FoodError("摄入克数必须大于 0")
    if qty > MAX_QUANTITY_G:
        raise FoodError("摄入克数超出合理范围")
    return (per * qty / Decimal(100)).quantize(KCAL_STEP, rounding=ROUND_HALF_UP)


def scale_nutrient(per_100g: Decimal | None, quantity_g: Decimal | int | float | str) -> Decimal | None:
    """按份量折算蛋白质/脂肪/碳水，保留两位小数。"""
    if per_100g is None:
        return None
    qty = _to_decimal(quantity_g, "摄入克数")
    return (_to_decimal(per_100g, "营养素") * qty / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


async def search_foods(
    session: AsyncSession,
    q: str = "",
    category: str | None = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> list[FoodItem]:
    """中文名 / 别名 / 拼音首字母三路匹配，精确名优先。"""
    limit = max(1, min(limit, DEFAULT_SEARCH_LIMIT))
    stmt = select(FoodItem).where(FoodItem.deleted_at.is_(None))

    keyword = (q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                FoodItem.name.ilike(pattern),
                FoodItem.alias.ilike(pattern),
                FoodItem.pinyin_abbr.ilike(f"{keyword.lower()}%"),
            )
        )
        # 排序不依赖 pg_trgm 的 similarity：C locale 下中文不产生 trigram，
        # similarity 恒为 0。改为「精确名 > 前缀 > 长度」的确定序。
        stmt = stmt.order_by(
            case(
                (FoodItem.name == keyword, 0),
                (FoodItem.name.ilike(f"{keyword}%"), 1),
                else_=2,
            ),
            func.length(FoodItem.name).asc(),
            FoodItem.id.asc(),
        )
    else:
        stmt = stmt.order_by(FoodItem.category.asc(), FoodItem.id.asc())

    if category:
        stmt = stmt.where(FoodItem.category == category)

    result = await session.execute(stmt.limit(limit))
    return list(result.scalars().all())
