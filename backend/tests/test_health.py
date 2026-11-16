"""健康汇总：聚合口径与软删除隔离。"""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.health import HealthDiet, HealthExercise, HealthSleep, HealthWeight
from app.services.health import (
    diet_summary,
    exercise_summary,
    overview,
    sleep_summary,
    weight_trend,
)

D = Decimal
DAY = date(2026, 11, 15)


async def _seed_diet(db):
    db.add_all(
        [
            HealthDiet(
                record_date=DAY,
                meal="breakfast",
                food_name="米饭",
                quantity_g=D("150.0"),
                calories_kcal=D("174.0"),
            ),
            HealthDiet(
                record_date=DAY,
                meal="lunch",
                food_name="番茄炒蛋",
                quantity_g=D("200.0"),
                calories_kcal=D("172.0"),
            ),
            HealthDiet(
                record_date=DAY,
                meal="lunch",
                food_name="清炒时蔬",
                quantity_g=D("100.0"),
                calories_kcal=D("45.0"),
            ),
        ]
    )
    await db.flush()


async def test_diet_summary_totals(db):
    await _seed_diet(db)
    summary = await diet_summary(db, DAY, DAY)
    assert summary["total_kcal"] == D("391.0")
    assert summary["record_count"] == 3
    assert summary["avg_kcal_per_day"] == D("391.0")


async def test_diet_summary_by_meal(db):
    await _seed_diet(db)
    summary = await diet_summary(db, DAY, DAY)
    assert summary["by_meal"]["breakfast"]["kcal"] == D("174.0")
    assert summary["by_meal"]["lunch"]["kcal"] == D("217.0")
    assert summary["by_meal"]["lunch"]["count"] == 2


async def test_diet_summary_averages_over_range(db):
    await _seed_diet(db)
    summary = await diet_summary(db, DAY, date(2026, 11, 17))
    # 3 天平均：391 / 3 = 130.333 -> 130.3
    assert summary["avg_kcal_per_day"] == D("130.3")


async def test_diet_summary_ignores_manual_flag_for_totals(db):
    db.add(
        HealthDiet(
            record_date=DAY,
            meal="dinner",
            food_name="自定义",
            quantity_g=D("100.0"),
            calories_kcal=D("300.0"),
            calories_manual=True,
        )
    )
    await db.flush()
    summary = await diet_summary(db, DAY, DAY)
    # 手动覆盖值必须原样计入统计
    assert summary["total_kcal"] == D("300.0")


async def test_diet_summary_excludes_soft_deleted(db):
    await _seed_diet(db)
    rows = (
        await db.execute(
            HealthDiet.__table__.select().where(HealthDiet.food_name == "米饭")
        )
    ).all()
    record = await db.get(HealthDiet, rows[0].id)
    record.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    assert (await diet_summary(db, DAY, DAY))["total_kcal"] == D("217.0")


async def test_weight_trend_is_ordered(db):
    db.add_all(
        [
            HealthWeight(record_date=date(2026, 11, 15), weight_kg=D("70.20")),
            HealthWeight(record_date=date(2026, 11, 13), weight_kg=D("70.80")),
            HealthWeight(record_date=date(2026, 11, 14), weight_kg=D("70.50"), body_fat_pct=D("18.5")),
        ]
    )
    await db.flush()
    trend = await weight_trend(db, date(2026, 11, 1), date(2026, 11, 30))
    assert [t["date"] for t in trend] == [
        date(2026, 11, 13),
        date(2026, 11, 14),
        date(2026, 11, 15),
    ]
    assert trend[0]["weight_kg"] == D("70.80")
    assert trend[1]["body_fat_pct"] == D("18.5")
    assert trend[2]["body_fat_pct"] is None


async def test_exercise_summary(db):
    db.add_all(
        [
            HealthExercise(record_date=DAY, exercise_type="跑步", duration_min=30, calories=D("260.0")),
            HealthExercise(record_date=DAY, exercise_type="力量", duration_min=45, calories=D("200.0")),
        ]
    )
    await db.flush()
    summary = await exercise_summary(db, DAY, DAY)
    assert summary["total_minutes"] == 75
    assert summary["record_count"] == 2
    assert summary["total_kcal"] == D("460.0")


async def test_sleep_summary(db):
    db.add_all(
        [
            HealthSleep(record_date=DAY, duration_min=420, quality=4),
            HealthSleep(record_date=date(2026, 11, 14), duration_min=480, quality=5),
        ]
    )
    await db.flush()
    summary = await sleep_summary(db, date(2026, 11, 14), DAY)
    assert summary["avg_minutes"] == 450
    assert summary["record_count"] == 2
    assert summary["avg_quality"] == D("4.5")


async def test_overview_combines_today(db):
    await _seed_diet(db)
    db.add(HealthWeight(record_date=DAY, weight_kg=D("70.20")))
    db.add(HealthExercise(record_date=DAY, exercise_type="跑步", duration_min=30))
    await db.flush()
    data = await overview(db, DAY)
    assert data["kcal_today"] == D("391.0")
    assert data["exercise_minutes"] == 30
    assert data["weight_kg"] == D("70.20")
    assert data["date"] == DAY
