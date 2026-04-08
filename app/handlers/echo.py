from aiogram import Router
from aiogram.types import Message
from services.userService import UserService

router = Router()

@router.message()
async def echoHandler(message: Message):
    await message.answer(UserService.getEchoText(message.text))
