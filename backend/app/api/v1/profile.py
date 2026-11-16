"""档案接口：个人信息（身份证脱敏）与人生大事。"""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import OwnerDep, SessionDep
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.core.security import SCOPE_REVEAL, AuthError, decode_token
from app.models.profile import LifeEvent, Profile
from app.schemas.auth import RevealTicket
from app.schemas.requests import LifeEventCreate, LifeEventUpdate, ProfileUpdate
from app.schemas.serializers import life_event_out
from app.services.clock import today
from app.services.crypto import CryptoError, decrypt_text
from app.services.lunar import constellation, lunar_text, lunar_to_solar, next_lunar_birthday, zodiac

router = APIRouter(tags=["profile"])


async def _get_profile(session) -> Profile:
    profile = await session.scalar(select(Profile).order_by(Profile.id).limit(1))
    if profile is None:
        raise NotFoundError("档案尚未初始化")
    return profile


def _profile_view(profile: Profile) -> dict:
    current = today()
    month = profile.lunar_birthday_month or 1
    day = profile.lunar_birthday_day or 1

    next_birthday = None
    days_left = None
    try:
        next_birthday = next_lunar_birthday(month, day, current)
        days_left = (next_birthday - current).days
    except Exception:  # noqa: BLE001
        pass

    solar = profile.solar_birthday
    return {
        "name": profile.name,
        "id_card_masked": profile.id_card_masked,
        "id_card_birthday": profile.id_card_birthday.isoformat() if profile.id_card_birthday else None,
        "lunar_birthday": f"农历{profile.lunar_birthday_year}年{month}月{day}日",
        "solar_birthday": solar.isoformat() if solar else None,
        "lunar_birthday_month": month,
        "lunar_birthday_day": day,
        "zodiac": zodiac(solar) if solar else None,
        "constellation": constellation(solar) if solar else None,
        "next_birthday": next_birthday.isoformat() if next_birthday else None,
        "days_to_birthday": days_left,
        "age": (current.year - solar.year) if solar else None,
        "phone": profile.phone,
        "email": profile.email,
        "wechat": profile.wechat,
        "blood_type": profile.blood_type,
        "address": profile.address,
        "avatar_url": profile.avatar_url,
        "height_cm": str(profile.height_cm) if profile.height_cm is not None else None,
        "bio": profile.bio,
        "today_lunar": lunar_text(current, with_year=False),
    }


@router.get("/profile")
async def get_profile(session: SessionDep, owner: OwnerDep) -> dict:
    return _profile_view(await _get_profile(session))


@router.patch("/profile")
async def update_profile(
    payload: ProfileUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    profile = await _get_profile(session)
    data = payload.model_dump(exclude_unset=True)

    month = data.pop("lunar_birthday_month", None)
    day = data.pop("lunar_birthday_day", None)

    for key, value in data.items():
        setattr(profile, key, value)

    if month or day:
        new_month = month or profile.lunar_birthday_month
        new_day = day or profile.lunar_birthday_day
        if new_month and new_day:
            profile.lunar_birthday_month = new_month
            profile.lunar_birthday_day = new_day
            profile.solar_birthday = lunar_to_solar(
                profile.lunar_birthday_year or 1992, new_month, new_day
            )

    await session.flush()
    return _profile_view(profile)


@router.post("/profile/reveal")
async def reveal_id_card(
    payload: RevealTicket, session: SessionDep, owner: OwnerDep
) -> dict:
    ticket = payload.ticket.strip()
    if not ticket:
        raise ForbiddenError("缺少验证票据")
    try:
        decode_token(ticket, settings.secret_key, expected_scope=SCOPE_REVEAL)
    except AuthError as exc:
        raise ForbiddenError(str(exc)) from exc

    profile = await _get_profile(session)
    if not profile.id_card_ciphertext:
        raise NotFoundError("未保存身份证号")

    try:
        plain = decrypt_text(profile.id_card_ciphertext, settings.id_card_key_bytes)
    except CryptoError as exc:
        raise ValidationError("身份证密文无法解密，可能密钥已变更，请重新初始化档案") from exc
    return {"id_card": plain}


# ---------- 人生大事 ----------
def _event_view(event: LifeEvent) -> dict:
    return {**life_event_out(event), "lunar": lunar_text(event.event_date, with_year=False)}


@router.get("/life-events")
async def list_life_events(session: SessionDep, owner: OwnerDep) -> dict:
    stmt = (
        select(LifeEvent)
        .where(LifeEvent.deleted_at.is_(None))
        .order_by(LifeEvent.event_date.desc(), LifeEvent.id.desc())
    )
    items = list((await session.execute(stmt)).scalars().all())
    return {"items": [_event_view(e) for e in items]}


@router.post("/life-events", status_code=201)
async def create_life_event(
    payload: LifeEventCreate, session: SessionDep, owner: OwnerDep
) -> dict:
    event = LifeEvent(**payload.model_dump())
    session.add(event)
    await session.flush()
    return _event_view(event)


@router.patch("/life-events/{event_id}")
async def update_life_event(
    event_id: int, payload: LifeEventUpdate, session: SessionDep, owner: OwnerDep
) -> dict:
    event = await session.get(LifeEvent, event_id)
    if event is None or event.deleted_at is not None:
        raise NotFoundError("事件不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, key, value)
    await session.flush()
    return _event_view(event)


@router.delete("/life-events/{event_id}")
async def delete_life_event(
    event_id: int, session: SessionDep, owner: OwnerDep
) -> dict:
    event = await session.get(LifeEvent, event_id)
    if event is None or event.deleted_at is not None:
        raise NotFoundError("事件不存在")
    event.deleted_at = datetime.now(timezone.utc)
    await session.flush()
    return {"ok": True}
