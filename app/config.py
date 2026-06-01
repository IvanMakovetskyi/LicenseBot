import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

class Settings:
    TOKEN = os.getenv("TOKEN")
    ADMINS = {int(admin) for admin in os.getenv("ADMINS").split(",") if admin}
    APP_ENV: str = os.getenv("APP_ENV", "prod")

settings = Settings()
