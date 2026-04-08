from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.userService import UserService
from keyboards.mainKeyboard import mainKeyboard

router = Router()

@router.message(Command("start"))
async def startHandler(message: Message):
    await message.answer(UserService.getStartText(), reply_markup=mainKeyboard)
