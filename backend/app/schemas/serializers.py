"""统一出参序列化：金额一律转字符串，日期转 ISO，避免前端浮点误差。"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

_MARKDOWN_NOISE = re.compile(r"[#>*_`~|]+")


def plain_excerpt(text: str | None, length: int = 120) -> str:
    """把 Markdown 压成一行纯文本摘要：去掉代码块与常见标记，避免首页出现 `#`、反引号。"""
    if not text:
        return ""
    without_code = re.sub(r"```.*?```", " ", text, flags=re.S)
    without_inline = re.sub(r"`[^`]*`", " ", without_code)
    cleaned = _MARKDOWN_NOISE.sub(" ", without_inline)
    cleaned = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        return cleaned[:length]
    # 纯代码块或特殊符号笔记：退化为原文摘要，保证列表至少能显示内容
    return re.sub(r"\s+", " ", text).strip()[:length]


def money(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.2f}"


def decimal_str(value: Decimal | None, places: int = 2) -> str | None:
    return None if value is None else f"{value:.{places}f}"


def dt(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def d(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def tag_out(tag) -> dict[str, Any]:
    return {"id": tag.id, "name": tag.name, "scope": tag.scope, "color": tag.color}


def todo_out(todo) -> dict[str, Any]:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "due_date": d(todo.due_date),
        "done": todo.done,
        "completed_at": dt(todo.completed_at),
        "system_key": todo.system_key,
        "frequency": todo.frequency,
        "interval": todo.interval,
        "weekdays": [int(x) for x in todo.weekdays.split(",")] if todo.weekdays else [],
        "until": d(todo.until),
        "parent_id": todo.parent_id,
        "sort_order": todo.sort_order,
        "tags": [tag_out(t) for t in todo.tags],
        "created_at": dt(todo.created_at),
        "updated_at": dt(todo.updated_at),
    }


def diary_out(diary) -> dict[str, Any]:
    return {
        "id": diary.id,
        "diary_date": d(diary.diary_date),
        "title": diary.title,
        "content": diary.content,
        "mood": diary.mood,
        "weather": diary.weather,
        "updated_at": dt(diary.updated_at),
    }


def note_out(note, *, with_content: bool = True) -> dict[str, Any]:
    data = {
        "id": note.id,
        "title": note.title,
        "is_pinned": note.is_pinned,
        "tags": [tag_out(t) for t in note.tags],
        "created_at": dt(note.created_at),
        "updated_at": dt(note.updated_at),
    }
    if with_content:
        data["content_md"] = note.content_md
    else:
        data["excerpt"] = plain_excerpt(note.content_md)
    return data


def food_out(food) -> dict[str, Any]:
    return {
        "id": food.id,
        "name": food.name,
        "alias": food.alias,
        "pinyin_abbr": food.pinyin_abbr,
        "category": food.category,
        "energy_kcal_per_100g": decimal_str(food.energy_kcal_per_100g, 2),
        "protein_g": decimal_str(food.protein_g, 2),
        "fat_g": decimal_str(food.fat_g, 2),
        "carb_g": decimal_str(food.carb_g, 2),
        "default_serving_g": decimal_str(food.default_serving_g, 1),
        "default_serving_label": food.default_serving_label,
        "is_system": food.is_system,
    }


def diet_out(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_date": d(record.record_date),
        "meal": record.meal,
        "food_item_id": record.food_item_id,
        "food_name": record.food_name,
        "quantity_g": decimal_str(record.quantity_g, 1),
        "calories_kcal": decimal_str(record.calories_kcal, 1),
        "calories_manual": record.calories_manual,
        "protein_g": decimal_str(record.protein_g, 2),
        "fat_g": decimal_str(record.fat_g, 2),
        "carb_g": decimal_str(record.carb_g, 2),
        "note": record.note,
    }


def exercise_out(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_date": d(record.record_date),
        "exercise_type": record.exercise_type,
        "duration_min": record.duration_min,
        "calories": decimal_str(record.calories, 1),
        "distance_km": decimal_str(record.distance_km, 2),
        "intensity": record.intensity,
        "note": record.note,
    }


def weight_out(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_date": d(record.record_date),
        "weight_kg": decimal_str(record.weight_kg, 2),
        "body_fat_pct": decimal_str(record.body_fat_pct, 1),
        "note": record.note,
    }


def sleep_out(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_date": d(record.record_date),
        "sleep_at": dt(record.sleep_at),
        "wake_at": dt(record.wake_at),
        "duration_min": record.duration_min,
        "quality": record.quality,
        "note": record.note,
    }


def account_out(account) -> dict[str, Any]:
    return {
        "id": account.id,
        "name": account.name,
        "account_type": account.account_type,
        "initial_balance": money(account.initial_balance),
        "currency": account.currency,
        "icon": account.icon,
        "color": account.color,
        "is_archived": account.is_archived,
        "sort_order": account.sort_order,
    }


def category_out(category) -> dict[str, Any]:
    return {
        "id": category.id,
        "name": category.name,
        "kind": category.kind,
        "icon": category.icon,
        "sort_order": category.sort_order,
    }


def transaction_out(tx, account_names: dict[int, str] | None = None) -> dict[str, Any]:
    names = account_names or {}
    return {
        "id": tx.id,
        "tx_type": tx.tx_type,
        "amount": money(tx.amount),
        "account_id": tx.account_id,
        "account_name": names.get(tx.account_id),
        "to_account_id": tx.to_account_id,
        "to_account_name": names.get(tx.to_account_id) if tx.to_account_id else None,
        "category_id": tx.category_id,
        "occurred_on": d(tx.occurred_on),
        "note": tx.note,
    }


def entertainment_out(item) -> dict[str, Any]:
    return {
        "id": item.id,
        "ent_type": item.ent_type,
        "status": item.status,
        "title": item.title,
        "cover_url": item.cover_url,
        "year": item.year,
        "rating": decimal_str(item.rating, 1),
        "progress": item.progress,
        "review": item.review,
        "external_url": item.external_url,
        "is_pinned": item.is_pinned,
        "sort_order": item.sort_order,
        "updated_at": dt(item.updated_at),
    }


def life_event_out(event) -> dict[str, Any]:
    return {
        "id": event.id,
        "title": event.title,
        "event_date": d(event.event_date),
        "event_type": event.event_type,
        "location": event.location,
        "description": event.description,
        "image_url": event.image_url,
        "is_highlight": event.is_highlight,
    }
