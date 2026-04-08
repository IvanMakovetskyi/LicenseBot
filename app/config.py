import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TOKEN = os.getenv("TOKEN")
    ADMINS = {838498434}

settings = Settings()
