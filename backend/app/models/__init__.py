"""集中导入全部模型，确保 Base.metadata 完整。"""

from app.models.auth import AppSetting, AuthCredential
from app.models.diary import Diary
from app.models.entertainment import ENT_STATUSES, ENT_TYPES, Entertainment
from app.models.finance import (
    TX_EXPENSE,
    TX_INCOME,
    TX_TRANSFER,
    Account,
    Category,
    Transaction,
)
from app.models.food import FOOD_CATEGORIES, FoodItem
from app.models.health import HealthDiet, HealthExercise, HealthSleep, HealthWeight
from app.models.note import Note, note_tag
from app.models.profile import LifeEvent, Profile
from app.models.tag import Tag
from app.models.todo import Todo, todo_tag

__all__ = [
    "Account",
    "AppSetting",
    "AuthCredential",
    "Category",
    "Diary",
    "ENT_STATUSES",
    "ENT_TYPES",
    "Entertainment",
    "FOOD_CATEGORIES",
    "FoodItem",
    "HealthDiet",
    "HealthExercise",
    "HealthSleep",
    "HealthWeight",
    "LifeEvent",
    "Note",
    "Profile",
    "TX_EXPENSE",
    "TX_INCOME",
    "TX_TRANSFER",
    "Tag",
    "Todo",
    "Transaction",
    "note_tag",
    "todo_tag",
]
