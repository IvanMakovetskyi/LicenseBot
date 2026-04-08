import asyncio
from config import settings
from aiogram import Bot, Dispatcher
from handlers.setupRouters import setupRouters
from database.db import initDb

async def main():
    initDb()

    bot = Bot(token=settings.TOKEN)
    dp = Dispatcher()

    setupRouters(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
