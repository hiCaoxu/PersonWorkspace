"""幂等种子：认证凭据、应用设置、个人档案、记账分类与账户、食物库。

用法（容器内）：python -m app.db.seed
"""

import asyncio
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_passcode
from app.db.seed_foods import seed_foods
from app.db.session import SessionLocal
from app.models.auth import AppSetting, AuthCredential
from app.models.finance import Account, Category
from app.models.profile import Profile
from app.services.crypto import CryptoError, decrypt_text, encrypt_text, mask_id_card
from app.services.lunar import lunar_to_solar

logger = logging.getLogger("app.seed")

# 证件登记生日为证号内的公历日期；真实生日为农历 1992 年 2 月 29 日
ID_CARD = "340322199202057851"
ID_CARD_BIRTHDAY = (1992, 2, 5)
LUNAR_BIRTHDAY = (1992, 2, 29)

DEFAULT_EXPENSE_CATEGORIES = [
    ("餐饮", "utensils"),
    ("交通", "bus"),
    ("购物", "shopping-bag"),
    ("居住", "home"),
    ("医疗", "heart-pulse"),
    ("娱乐", "clapperboard"),
    ("学习", "book-open"),
    ("人情", "gift"),
    ("其他", "ellipsis"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("工资", "wallet"),
    ("奖金", "award"),
    ("理财", "trending-up"),
    ("其他", "ellipsis"),
]

DEFAULT_ACCOUNTS = [
    ("现金", "cash", Decimal("0.00"), "banknote"),
    ("微信", "wechat", Decimal("0.00"), "message-circle"),
    ("支付宝", "alipay", Decimal("0.00"), "smartphone"),
    ("银行卡", "bank", Decimal("0.00"), "credit-card"),
]

DEFAULT_SETTINGS = {
    "daily_system_todos_enabled": "true",
    "food_library_version": "cn_v6_subset_1",
}


async def _count(session: AsyncSession, model) -> int:
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


async def seed_credential(session: AsyncSession) -> bool:
    if await _count(session, AuthCredential) > 0:
        return False
    session.add(AuthCredential(passcode_hash=hash_passcode(settings.admin_password)))
    await session.flush()
    logger.info("已写入初始登录口令（来自 ADMIN_PASSWORD）")
    return True


async def seed_settings(session: AsyncSession) -> int:
    created = 0
    for key, value in DEFAULT_SETTINGS.items():
        exists = await session.scalar(select(AppSetting).where(AppSetting.key == key))
        if exists:
            continue
        session.add(AppSetting(key=key, value=value))
        created += 1
    await session.flush()
    return created


async def seed_profile_data(session: AsyncSession) -> bool:
    existing = await session.scalar(select(Profile).order_by(Profile.id).limit(1))
    if existing is not None:
        # 密钥轮换后用种子证件号重新加密，避免揭示接口 500。
        try:
            decrypt_text(existing.id_card_ciphertext, settings.id_card_key_bytes)
        except (CryptoError, TypeError):
            existing.id_card_ciphertext = encrypt_text(ID_CARD, settings.id_card_key_bytes)
            logger.info("检测到身份证密钥变更，已用当前密钥重新加密")
            return True
        return False

    solar_birthday = lunar_to_solar(*LUNAR_BIRTHDAY)
    session.add(
        Profile(
            name="曹旭",
            id_card_ciphertext=encrypt_text(ID_CARD, settings.id_card_key_bytes),
            id_card_masked=mask_id_card(ID_CARD),
            id_card_birthday=date(*ID_CARD_BIRTHDAY),
            lunar_birthday_year=LUNAR_BIRTHDAY[0],
            lunar_birthday_month=LUNAR_BIRTHDAY[1],
            lunar_birthday_day=LUNAR_BIRTHDAY[2],
            solar_birthday=solar_birthday,
            phone="13349206253",
            email="hicaoxu@qq.com",
            wechat="hellocaoxu",
            blood_type="B",
            address="安徽省蚌埠市五河县双忠庙镇邓圩村西刘组116号",
        )
    )
    await session.flush()
    logger.info("已写入个人档案，农历生日换算公历=%s", solar_birthday)
    return True


async def seed_finance(session: AsyncSession) -> dict:
    created_cat = 0
    for order, (name, icon) in enumerate(DEFAULT_EXPENSE_CATEGORIES):
        if await session.scalar(select(Category).where(Category.name == name, Category.kind == "expense")):
            continue
        session.add(Category(name=name, kind="expense", icon=icon, sort_order=order))
        created_cat += 1

    for order, (name, icon) in enumerate(DEFAULT_INCOME_CATEGORIES):
        if await session.scalar(select(Category).where(Category.name == name, Category.kind == "income")):
            continue
        session.add(Category(name=name, kind="income", icon=icon, sort_order=order))
        created_cat += 1

    created_acc = 0
    for order, (name, acc_type, balance, icon) in enumerate(DEFAULT_ACCOUNTS):
        if await session.scalar(select(Account).where(Account.name == name)):
            continue
        session.add(
            Account(
                name=name,
                account_type=acc_type,
                initial_balance=balance,
                icon=icon,
                sort_order=order,
            )
        )
        created_acc += 1

    await session.flush()
    return {"categories": created_cat, "accounts": created_acc}


async def seed_all(session: AsyncSession) -> dict:
    credential = await seed_credential(session)
    setting_count = await seed_settings(session)
    profile = await seed_profile_data(session)
    finance = await seed_finance(session)
    foods = await seed_foods(session)
    return {
        "credential_created": credential,
        "settings_created": setting_count,
        "profile_created": profile,
        **finance,
        "foods_loaded": foods,
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with SessionLocal() as session:
        async with session.begin():
            result = await seed_all(session)
    logger.info("种子完成: %s", result)


if __name__ == "__main__":
    asyncio.run(main())
