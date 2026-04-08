from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def echoHandler(message: Message):
    await message.answer(f"You said: {message.text}")
