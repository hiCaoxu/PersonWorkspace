"""食物库导入：按 name 幂等 upsert，可重复执行。"""

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodItem

DATA_FILE = Path(__file__).resolve().parent / "data" / "foods_cn_v6.json"


def load_food_rows() -> list[dict]:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    fields: list[str] = payload["fields"]
    source = payload.get("source", "")
    rows: list[dict] = []

    for raw in payload["items"]:
        item = dict(zip(fields, raw, strict=True))
        rows.append(
            {
                "name": item["name"],
                "alias": item["alias"] or None,
                "pinyin_abbr": item["pinyin"] or None,
                "category": item["category"],
                "energy_kcal_per_100g": Decimal(str(item["kcal"])),
                "protein_g": Decimal(str(item["protein"])),
                "fat_g": Decimal(str(item["fat"])),
                "carb_g": Decimal(str(item["carb"])),
                "default_serving_g": Decimal(str(item["serving_g"])),
                "default_serving_label": item["serving_label"] or None,
                "is_system": True,
                "note": source,
            }
        )
    return rows


async def seed_foods(session: AsyncSession) -> int:
    rows = load_food_rows()
    if not rows:
        return 0

    stmt = pg_insert(FoodItem).values(rows).on_conflict_do_nothing(index_elements=["name"])
    await session.execute(stmt)
    await session.flush()
    return len(rows)
