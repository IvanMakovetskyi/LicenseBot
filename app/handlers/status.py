from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("status"))
async def statusHandler(message: Message):
    await message.answer("Your status is unknown :(")
