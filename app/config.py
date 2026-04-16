import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TOKEN = os.getenv("TOKEN")
    ADMINS = {838498434, 522072812, 804182735}

settings = Settings()
