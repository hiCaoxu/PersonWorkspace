"""请求体模型。"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

RecurrenceFrequency = Literal["none", "daily", "weekly", "monthly", "yearly"]


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    frequency: RecurrenceFrequency = "none"
    interval: int = Field(default=1, ge=1, le=365)
    weekdays: list[int] = Field(default_factory=list)
    until: date | None = None
    tag_ids: list[int] = Field(default_factory=list)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    frequency: RecurrenceFrequency | None = None
    interval: int | None = Field(default=None, ge=1, le=365)
    weekdays: list[int] | None = None
    until: date | None = None
    tag_ids: list[int] | None = None


class DiaryUpdate(BaseModel):
    content: str | None = None
    mood: str | None = Field(default=None, max_length=16)
    weather: str | None = Field(default=None, max_length=16)


class NoteCreate(BaseModel):
    title: str = Field(default="无标题", max_length=200)
    content_md: str = ""
    tag_ids: list[int] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content_md: str | None = None
    tag_ids: list[int] | None = None
    is_pinned: bool | None = None


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    scope: Literal["todo", "note"] = "todo"
    color: str = Field(default="#B08968", max_length=16)


class FoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    alias: str | None = Field(default=None, max_length=200)
    category: str = Field(default="菜肴", max_length=16)
    energy_kcal_per_100g: Decimal = Field(ge=0, le=1000)
    default_serving_g: Decimal | None = Field(default=None, gt=0, le=5000)
    default_serving_label: str | None = Field(default=None, max_length=16)


class DietCreate(BaseModel):
    record_date: date
    meal: Literal["breakfast", "lunch", "dinner", "snack"] = "lunch"
    food_item_id: int | None = None
    food_name: str | None = Field(default=None, max_length=64)
    quantity_g: Decimal = Field(gt=0, le=5000)
    calories_kcal: Decimal | None = Field(default=None, ge=0, le=10000)
    note: str | None = None


class ExerciseCreate(BaseModel):
    record_date: date
    exercise_type: str = Field(min_length=1, max_length=32)
    duration_min: int = Field(ge=0, le=1440)
    calories: Decimal | None = Field(default=None, ge=0, le=20000)
    distance_km: Decimal | None = Field(default=None, ge=0, le=500)
    intensity: str | None = Field(default=None, max_length=16)
    note: str | None = None


class WeightCreate(BaseModel):
    record_date: date
    weight_kg: Decimal = Field(gt=0, le=400)
    body_fat_pct: Decimal | None = Field(default=None, ge=0, le=80)
    note: str | None = None


class SleepCreate(BaseModel):
    record_date: date
    sleep_at: str | None = None
    wake_at: str | None = None
    duration_min: int = Field(ge=0, le=1440)
    quality: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    account_type: str = Field(default="bank", max_length=16)
    initial_balance: Decimal = Field(default=Decimal("0.00"))
    icon: str | None = Field(default=None, max_length=32)
    color: str | None = Field(default=None, max_length=16)
    sort_order: int = 0


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=32)
    account_type: str | None = Field(default=None, max_length=16)
    initial_balance: Decimal | None = None
    icon: str | None = None
    color: str | None = None
    is_archived: bool | None = None
    sort_order: int | None = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    kind: Literal["income", "expense"] = "expense"
    icon: str | None = Field(default=None, max_length=32)
    sort_order: int = 0


class TransactionCreate(BaseModel):
    tx_type: Literal["income", "expense", "transfer"]
    amount: Decimal = Field(gt=0, le=Decimal("9999999999.99"))
    account_id: int
    to_account_id: int | None = None
    category_id: int | None = None
    occurred_on: date
    note: str | None = None


class EntertainmentCreate(BaseModel):
    ent_type: Literal["movie", "tv", "documentary", "podcast", "book"] = "movie"
    status: Literal["want", "doing", "done"] = "want"
    title: str = Field(min_length=1, max_length=200)
    cover_url: str | None = Field(default=None, max_length=512)
    year: int | None = Field(default=None, ge=1900, le=2100)
    rating: Decimal | None = Field(default=None, ge=0, le=10)
    progress: int = Field(default=0, ge=0, le=100)
    review: str | None = None
    external_url: str | None = Field(default=None, max_length=512)


class EntertainmentUpdate(BaseModel):
    ent_type: Literal["movie", "tv", "documentary", "podcast", "book"] | None = None
    status: Literal["want", "doing", "done"] | None = None
    title: str | None = Field(default=None, max_length=200)
    cover_url: str | None = None
    year: int | None = None
    rating: Decimal | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    review: str | None = None
    external_url: str | None = None
    sort_order: int | None = None


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    wechat: str | None = Field(default=None, max_length=64)
    blood_type: str | None = Field(default=None, max_length=8)
    address: str | None = Field(default=None, max_length=256)
    height_cm: Decimal | None = None
    bio: str | None = None
    lunar_birthday_month: int | None = Field(default=None, ge=1, le=12)
    lunar_birthday_day: int | None = Field(default=None, ge=1, le=30)


class LifeEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    event_date: date
    event_type: str = Field(default="other", max_length=16)
    location: str | None = Field(default=None, max_length=128)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=512)
    is_highlight: bool = False


class LifeEventUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    event_date: date | None = None
    event_type: str | None = None
    location: str | None = None
    description: str | None = None
    image_url: str | None = None
    is_highlight: bool | None = None
