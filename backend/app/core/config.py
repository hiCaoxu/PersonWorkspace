"""应用配置：全部来自环境变量，敏感项不落代码。"""

import base64
import hashlib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "个人工作台"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://pwb:pwb_pass@db:5432/personal_workbench"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    secret_key: str = "dev-only-change-me-in-production"
    admin_password: str = "admin12345"
    id_card_key: str = ""

    session_cookie: str = "pwb_session"
    token_ttl_minutes: int = 60 * 24 * 7
    reveal_ttl_minutes: int = 5
    cookie_secure: bool = False

    login_max_attempts: int = 5
    login_window_minutes: int = 15

    upload_dir: str = "/data/uploads"
    upload_max_mb: int = 10
    thumbnail_width: int = 400

    timezone: str = "Asia/Shanghai"
    daily_system_todos: bool = True

    @property
    def id_card_key_bytes(self) -> bytes:
        """优先用环境变量提供的 base64 32 字节密钥，否则从 SECRET_KEY 派生。"""
        raw = (self.id_card_key or "").strip()
        if raw:
            try:
                decoded = base64.b64decode(raw)
            except Exception:  # noqa: BLE001
                decoded = b""
            if len(decoded) == 32:
                return decoded
            # 允许直接写 32 字符明文
            encoded = raw.encode("utf-8")
            if len(encoded) == 32:
                return encoded
        return hashlib.sha256(f"{self.secret_key}:idcard".encode()).digest()

    @property
    def upload_max_bytes(self) -> int:
        return self.upload_max_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
