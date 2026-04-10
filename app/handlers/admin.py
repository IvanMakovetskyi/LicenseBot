from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from services.clientService import clientService
from keyboards.adminKeyboard import adminKeyboard
from config import settings

router = Router()

@router.message(Command("admin"))
async def admiPanel(message: Message):
    if message.from_user.id not in settings.ADMINS:
        await message.answer("You are not admin.")
        return

    print(f"Id in AdminPanel: {message.from_user.id}")
    await message.answer("Admin panel", reply_markup=adminKeyboard)

@router.callback_query(F.data == "admin_clients")
async def adminClients(callback: CallbackQuery):

    clients = await clientService.getAllClients()

    if not clients:
        await callback.message.answer("No clients found.")
        await callback.answer()
        return

    text = "Clients:\n\n"

    for i, client in enumerate(clients, start=1):
        text += (
            f"{i}. {client['full_name']} | "
            f"{client['us_state']} | "
            f"{client['status']}\n"
        )

    await callback.message.answer(text)
    await callback.answer()
