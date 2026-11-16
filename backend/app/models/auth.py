"""认证与全局设置。"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, TimestampMixin


class AuthCredential(Base, PkMixin, TimestampMixin):
    """单用户口令，全表只有一行。"""

    __tablename__ = "auth_credential"

    passcode_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class AppSetting(Base, PkMixin, TimestampMixin):
    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
