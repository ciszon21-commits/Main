from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class DatabaseConfig:
    ENGINE: str
    NAME: str
    USER: str = ""
    PASSWORD: str = ""
    HOST: str = ""
    PORT: str = ""
    OPTIONS: dict[str, Any] = field(default_factory=dict)

    def to_django(self) -> dict[str, Any]:
        return {
            "ENGINE": self.ENGINE,
            "NAME": self.NAME,
            "USER": self.USER,
            "PASSWORD": self.PASSWORD,
            "HOST": self.HOST,
            "PORT": self.PORT,
            "OPTIONS": self.OPTIONS,
        }

    def merged_non_empty(self, other: "DatabaseConfig") -> "DatabaseConfig":
        """
        self 為 base，只用 other 內「有值」的欄位覆蓋，避免空字串覆蓋掉 base。
        """
        base = asdict(self)
        override = asdict(other)

        for k, v in override.items():
            if v is None:
                continue
            if isinstance(v, str) and v == "":
                continue
            if isinstance(v, dict) and v == {}:
                continue
            base[k] = v

        return DatabaseConfig(**base)


@dataclass(frozen=True)
class AppSettings:
    DATABASES: dict[str, DatabaseConfig] = field(
        default_factory=lambda: {
            "default": DatabaseConfig(
                ENGINE="django.db.backends.sqlite3",
                NAME="db.sqlite3",
            )
        }
    )

    SECRET_KEY: str = "django-insecure--%dbcahm$h45=qeyio&^8$*iz1!-tnby))#oeowkq0@90c#k!("

    ALLOWED_HOSTS: list[str] = field(default_factory=lambda: ["localhost", "127.0.0.1", "0.0.0.0"])
    DATA_UPLOAD_MAX_NUMBER_FILES: int = 2000
    DEBUG: bool = True

    STAGE_INSTALLED_APPS: list[str] = field(default_factory=list)
    STAGE_MIDDLEWARES: list[str] = field(default_factory=list)
    STAGE_READ_DB_LABELS: list[str] = field(default_factory=list)
    STAGE_WRITE_DB_LABELS: list[str] = field(default_factory=list)
    STAGE_MIGRATE_DB_LABELS: list[str] = field(default_factory=list)

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str | None = None

    SINO_AUTH_SERVICE_TOKEN: str | None = None
    SINO_AUTH_SERVICE_DOMAIN: str | None = None
    SINO_AUTH_SERVICE_APP_PATH: str | None = None

    ANYTHINGLLM_KEY: str | None = None

    EMAIL_HOST: str | None = None
    EMAIL_HOST_USER: str | None = None
    EMAIL_HOST_PASSWORD: str | None = None

    SYSTEM_EMAIL: str = "測試郵件"
    NOTIFY_EMAIL_NAME: str = "測試開發者"
    NOTIFY_EMAIL: str = "通知郵件"

    AUTHENTICATION_BACKENDS: list[str] = field(
        default_factory=lambda: [
            "CoDevStudio.backends.sino_remote_user_backend.SinoRemoteUserBackend",
            "django.contrib.auth.backends.ModelBackend",
        ]
    )

    EMAIL_BACKEND: str = "django.core.mail.backends.console.EmailBackend"
