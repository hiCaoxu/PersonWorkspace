"""食物库：热量折算精度与三路搜索。"""

from decimal import Decimal

import pytest

from app.models.food import FoodItem
from app.services.food import FoodError, compute_kcal, scale_nutrient, search_foods


def test_compute_kcal_basic():
    assert compute_kcal(Decimal("116"), Decimal("150")) == Decimal("174.0")


def test_compute_kcal_per_100g_is_identity():
    assert compute_kcal(Decimal("116"), Decimal("100")) == Decimal("116.0")


def test_compute_kcal_round_half_up():
    # 52 × 33 / 100 = 17.16 -> 17.2
    assert compute_kcal(52, 33) == Decimal("17.2")
    # 45 × 11 / 100 = 4.95 -> 5.0
    assert compute_kcal(45, 11) == Decimal("5.0")


def test_compute_kcal_accepts_strings_and_ints():
    assert compute_kcal("116", 150) == Decimal("174.0")


def test_compute_kcal_rejects_zero_quantity():
    with pytest.raises(FoodError):
        compute_kcal(116, 0)


def test_compute_kcal_rejects_negative_energy():
    with pytest.raises(FoodError):
        compute_kcal(-1, 100)


def test_compute_kcal_rejects_absurd_quantity():
    with pytest.raises(FoodError):
        compute_kcal(116, 99999)


def test_scale_nutrient():
    assert scale_nutrient(Decimal("2.60"), 150) == Decimal("3.90")
    assert scale_nutrient(None, 150) is None


async def _seed(db):
    db.add_all(
        [
            FoodItem(
                name="米饭",
                alias="白米饭,大米饭",
                pinyin_abbr="mf",
                category="谷薯类",
                energy_kcal_per_100g=Decimal("116.00"),
                protein_g=Decimal("2.60"),
                default_serving_g=Decimal("150.0"),
                default_serving_label="1碗",
                is_system=True,
            ),
            FoodItem(
                name="西红柿",
                alias="番茄",
                pinyin_abbr="xhs",
                category="蔬果",
                energy_kcal_per_100g=Decimal("15.00"),
                is_system=True,
            ),
            FoodItem(
                name="番茄炒蛋",
                alias="西红柿炒鸡蛋",
                pinyin_abbr="fqcd",
                category="菜肴",
                energy_kcal_per_100g=Decimal("86.00"),
                is_system=True,
            ),
            FoodItem(
                name="已删除食物",
                pinyin_abbr="ysc",
                category="菜肴",
                energy_kcal_per_100g=Decimal("100.00"),
                is_system=True,
                deleted_at=None,
            ),
        ]
    )
    await db.flush()


async def test_search_by_name(db):
    await _seed(db)
    results = await search_foods(db, "米饭")
    assert results
    assert results[0].name == "米饭"


async def test_search_by_alias(db):
    await _seed(db)
    names = [f.name for f in await search_foods(db, "番茄")]
    assert "西红柿" in names
    assert "番茄炒蛋" in names


async def test_search_by_pinyin_abbr(db):
    await _seed(db)
    results = await search_foods(db, "mf")
    assert [f.name for f in results] == ["米饭"]


async def test_exact_name_ranks_first(db):
    await _seed(db)
    results = await search_foods(db, "西红柿")
    assert results[0].name == "西红柿"


async def test_search_respects_limit(db):
    await _seed(db)
    results = await search_foods(db, limit=1)
    assert len(results) == 1


async def test_search_filters_category(db):
    await _seed(db)
    results = await search_foods(db, "番", category="蔬果")
    assert [f.name for f in results] == ["西红柿"]


async def test_soft_deleted_food_is_hidden(db):
    await _seed(db)
    from datetime import datetime, timezone

    item = (await search_foods(db, "已删除"))[0]
    item.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    assert await search_foods(db, "已删除") == []


async def test_empty_keyword_returns_list(db):
    await _seed(db)
    assert len(await search_foods(db, "")) == 4
