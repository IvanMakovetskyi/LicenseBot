import asyncio
import logging
from config import settings
from aiogram import Bot, Dispatcher
from handlers.setupRouters import setupRouters
from database.db import close_pool, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


async def main():
    await init_db()

    bot = Bot(token=settings.TOKEN)
    dp = Dispatcher()

    setupRouters(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
