import os
from pathlib import Path

from dotenv import load_dotenv # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "app" / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


class Settings:
    TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or "").strip()
    if not TOKEN:
        raise RuntimeError("Missing required environment variable: BOT_TOKEN (or TOKEN)")

    _admins_raw = _require_env("ADMINS")
    ADMINS = {int(admin.strip()) for admin in _admins_raw.split(",") if admin.strip()}
    DATABASE_URL = _require_env("DATABASE_URL")
    APP_ENV: str = os.getenv("APP_ENV", "prod")


settings = Settings()
