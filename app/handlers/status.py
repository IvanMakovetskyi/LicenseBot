from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from services.userService import UserService

router = Router()

@router.message(Command("status"))
async def statusHandler(message: Message):
    await message.answer(UserService.getStatusText())

@router.message(F.text == "Status")
async def statusButtonHandler(message: Message):
    await message.answer(UserService.getStatusText())
