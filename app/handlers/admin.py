from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.adminKeyboard import adminKeyboard
from config import settings

router = Router()

@router.message(Command("admin"))
async def admiPanel(message: Message):
    if message.from_user.id not in settings.ADMINS:
        await message.answer("You are not admin.")
        return

    await message.answer("Admin panel", reply_markup=adminKeyboard)

@router.callback_query(F.data == "send_greeting")
async def sendGreeting(callback: CallbackQuery):
    await callback.message.answer("Hello! This is a greeting message.")
    await callback.answer()
