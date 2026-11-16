"""健康接口：锻炼 / 饮食 / 体重 / 睡眠 的增删改与汇总。"""

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import OwnerDep, SessionDep
from app.core.errors import NotFoundError, ValidationError
from app.models.food import FoodItem
from app.models.health import HealthDiet, HealthExercise, HealthSleep, HealthWeight
from app.schemas.requests import DietCreate, ExerciseCreate, SleepCreate, WeightCreate
from app.schemas.serializers import diet_out, exercise_out, sleep_out, weight_out
from app.services import health as summary_service
from app.services.clock import today
from app.services.food import compute_kcal, scale_nutrient
from app.services.system_todos import SystemKey, complete_system_todo

router = APIRouter(prefix="/health", tags=["health"])


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"时间格式不正确: {value}") from exc


async def _get(session, model, record_id: int):
    record = await session.get(model, record_id)
    if record is None or record.deleted_at is not None:
        raise NotFoundError("记录不存在")
    return record


@router.get("/exercises")
async def list_exercises(
    session: SessionDep, start: date, end: date, owner: OwnerDep
) -> dict:
    stmt = (
        select(HealthExercise)
        .where(
            HealthExercise.deleted_at.is_(None),
            HealthExercise.record_date >= start,
            HealthExercise.record_date <= end,
        )
        .order_by(HealthExercise.record_date.desc(), HealthExercise.id.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [exercise_out(r) for r in items]}


@router.post("/exercises", status_code=201)
async def create_exercise(
    payload: ExerciseCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = HealthExercise(**payload.model_dump())
    session.add(record)
    await session.flush()
    await complete_system_todo(session, SystemKey.EXERCISE, payload.record_date)
    return exercise_out(record)


@router.patch("/exercises/{record_id}")
async def update_exercise(
    record_id: int, payload: ExerciseCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = await _get(session, HealthExercise, record_id)
    for key, value in payload.model_dump().items():
        setattr(record, key, value)
    await session.flush()
    return exercise_out(record)


@router.delete("/exercises/{record_id}")
async def delete_exercise(record_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    record = await _get(session, HealthExercise, record_id)
    record.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


@router.get("/diets")
async def list_diets(
    session: SessionDep, start: date, end: date, owner: OwnerDep
) -> dict:
    stmt = (
        select(HealthDiet)
        .where(
            HealthDiet.deleted_at.is_(None),
            HealthDiet.record_date >= start,
            HealthDiet.record_date <= end,
        )
        .order_by(HealthDiet.record_date.desc(), HealthDiet.id.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [diet_out(r) for r in items]}


@router.post("/diets", status_code=201)
async def create_diet(payload: DietCreate, session: SessionDep, owner: OwnerDep) -> dict:
    food: FoodItem | None = None
    if payload.food_item_id is not None:
        food = await session.get(FoodItem, payload.food_item_id)
        if food is None or food.deleted_at is not None:
            raise NotFoundError("食物不存在")

    name = (payload.food_name or (food.name if food else "")).strip()
    if not name:
        raise ValidationError("请填写食物名称或选择食物")

    quantity = Decimal(payload.quantity_g)
    if payload.calories_kcal is not None:
        kcal = Decimal(payload.calories_kcal)
        manual = True
    elif food is not None:
        kcal = compute_kcal(food.energy_kcal_per_100g, quantity)
        manual = False
    else:
        raise ValidationError("手动录入食物时请填写热量")

    record = HealthDiet(
        record_date=payload.record_date,
        meal=payload.meal,
        food_item_id=food.id if food else None,
        food_name=name,
        quantity_g=quantity,
        calories_kcal=kcal,
        calories_manual=manual,
        protein_g=scale_nutrient(food.protein_g, quantity) if food else None,
        fat_g=scale_nutrient(food.fat_g, quantity) if food else None,
        carb_g=scale_nutrient(food.carb_g, quantity) if food else None,
        note=payload.note,
    )
    session.add(record)
    await session.flush()
    await complete_system_todo(session, SystemKey.DIET, payload.record_date)
    return diet_out(record)


@router.patch("/diets/{record_id}")
async def update_diet(
    record_id: int, payload: DietCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = await _get(session, HealthDiet, record_id)
    record.record_date = payload.record_date
    record.meal = payload.meal
    record.food_name = (payload.food_name or record.food_name).strip()
    record.quantity_g = Decimal(payload.quantity_g)
    record.note = payload.note

    if payload.calories_kcal is not None:
        record.calories_kcal = Decimal(payload.calories_kcal)
        record.calories_manual = True
    elif payload.food_item_id is not None:
        food = await session.get(FoodItem, payload.food_item_id)
        if food is None or food.deleted_at is not None:
            raise NotFoundError("食物不存在")
        record.food_item_id = food.id
        record.calories_kcal = compute_kcal(food.energy_kcal_per_100g, record.quantity_g)
        record.calories_manual = False
        record.protein_g = scale_nutrient(food.protein_g, record.quantity_g)
        record.fat_g = scale_nutrient(food.fat_g, record.quantity_g)
        record.carb_g = scale_nutrient(food.carb_g, record.quantity_g)

    await session.flush()
    return diet_out(record)


@router.delete("/diets/{record_id}")
async def delete_diet(record_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    record = await _get(session, HealthDiet, record_id)
    record.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


@router.get("/weights")
async def list_weights(
    session: SessionDep, start: date, end: date, owner: OwnerDep
) -> dict:
    stmt = (
        select(HealthWeight)
        .where(
            HealthWeight.deleted_at.is_(None),
            HealthWeight.record_date >= start,
            HealthWeight.record_date <= end,
        )
        .order_by(HealthWeight.record_date.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [weight_out(r) for r in items]}


@router.post("/weights", status_code=201)
async def create_weight(
    payload: WeightCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = HealthWeight(**payload.model_dump())
    session.add(record)
    await session.flush()
    return weight_out(record)


@router.patch("/weights/{record_id}")
async def update_weight(
    record_id: int, payload: WeightCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = await _get(session, HealthWeight, record_id)
    for key, value in payload.model_dump().items():
        setattr(record, key, value)
    await session.flush()
    return weight_out(record)


@router.delete("/weights/{record_id}")
async def delete_weight(record_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    record = await _get(session, HealthWeight, record_id)
    record.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


@router.get("/sleeps")
async def list_sleeps(
    session: SessionDep, start: date, end: date, owner: OwnerDep
) -> dict:
    stmt = (
        select(HealthSleep)
        .where(
            HealthSleep.deleted_at.is_(None),
            HealthSleep.record_date >= start,
            HealthSleep.record_date <= end,
        )
        .order_by(HealthSleep.record_date.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [sleep_out(r) for r in items]}


@router.post("/sleeps", status_code=201)
async def create_sleep(
    payload: SleepCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = HealthSleep(
        record_date=payload.record_date,
        sleep_at=_parse_dt(payload.sleep_at),
        wake_at=_parse_dt(payload.wake_at),
        duration_min=payload.duration_min,
        quality=payload.quality,
        note=payload.note,
    )
    session.add(record)
    await session.flush()
    return sleep_out(record)


@router.patch("/sleeps/{record_id}")
async def update_sleep(
    record_id: int, payload: SleepCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    record = await _get(session, HealthSleep, record_id)
    record.record_date = payload.record_date
    record.sleep_at = _parse_dt(payload.sleep_at)
    record.wake_at = _parse_dt(payload.wake_at)
    record.duration_min = payload.duration_min
    record.quality = payload.quality
    record.note = payload.note
    await session.flush()
    return sleep_out(record)


@router.delete("/sleeps/{record_id}")
async def delete_sleep(record_id: int, session: SessionDep, owner: OwnerDep) -> dict:
    record = await _get(session, HealthSleep, record_id)
    record.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}


@router.get("/summary")
async def health_summary(
    session: SessionDep, start: date, end: date, owner: OwnerDep
) -> dict:
    diet = await summary_service.diet_summary(session, start, end)
    exercise = await summary_service.exercise_summary(session, start, end)
    sleep = await summary_service.sleep_summary(session, start, end)
    weight = await summary_service.weight_trend(session, start, end)
    overview_data = await summary_service.overview(session, today())
    return {
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "diet": {k: (str(v) if isinstance(v, Decimal) else v) for k, v in diet.items() if k != "by_meal"},
        "diet_by_meal": {
            meal: {"kcal": str(v["kcal"]), "count": v["count"]} for meal, v in diet["by_meal"].items()
        },
        "exercise": {k: (str(v) if isinstance(v, Decimal) else v) for k, v in exercise.items()},
        "sleep": {k: (str(v) if isinstance(v, Decimal) else v) for k, v in sleep.items()},
        "weight": [
            {
                "date": row["date"].isoformat(),
                "weight_kg": str(row["weight_kg"]),
                "body_fat_pct": str(row["body_fat_pct"]) if row["body_fat_pct"] is not None else None,
            }
            for row in weight
        ],
        "today": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in overview_data.items()
        },
    }
