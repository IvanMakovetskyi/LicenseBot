from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from services.clientService import clientService
from keyboards.adminKeyboard import adminKeyboard
from config import settings

router = Router()

@router.message(Command("admin"))
async def admiPanel(message: Message):
    print (f"Admin Message from ID: {message.from_user.id}")
    if message.from_user.id not in settings.ADMINS:
        await message.answer("У вас нет админ прав")
        return

    await message.answer("Админ панель:", reply_markup=adminKeyboard)

@router.callback_query(F.data == "admin_clients")
async def adminClients(callback: CallbackQuery):

    clients = await clientService.getAllClients()

    if not clients:
        await callback.message.answer("Клиенты не найдены")
        await callback.answer()
        return

    text = "Клиенты:\n\n"

    for i, client in enumerate(clients, start=1):
        text += (
            f"{i}. {client['full_name']} | "
            f"{client['us_state']} | "
            f"{client['status']}\n"
        )

    await callback.message.answer(text)
    await callback.answer()
