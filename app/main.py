import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Hello! Bot is working.")

@dp.message(Command("status"))
async def status_handler(message: Message):
    await message.answer("Your status is unknown :(")

@dp.message(F.document)
async def handle_document(message: Message, bot: Bot):
    document = message.document

    os.makedirs("documents", exist_ok=True)

    file_id = document.file_id
    file_name = document.file_name
    file_size = document.file_size

    await message.answer(f"Recieved file: {file_name}")

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    destination = f"documents/{file_name}"
    await bot.download_file(file_path, destination=destination)

    await message.answer("Document saved successfully.")


@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"Hey, you said: {message.text}")

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
