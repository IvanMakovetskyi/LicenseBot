from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from services.clientService import clientService
from keyboards.adminKeyboard import adminKeyboard
from config import settings

router = Router()
MAX_MESSAGE_LEN = 4000

@router.message(Command("admin"))
async def admiPanel(message: Message):
    if not message.from_user:
        return

    if message.from_user.id not in settings.ADMINS:
        await message.answer("У вас нет админ прав")
        return

    envLabel = " (DEV mode)" if settings.APP_ENV == "dev" else ""
    await message.answer(f"Админ панель:{envLabel}", reply_markup=adminKeyboard)

@router.callback_query(F.data == "admin_clients")
async def adminClients(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id not in settings.ADMINS:
        await callback.answer("У вас нет админ прав", show_alert=True)
        return

    if not callback.message:
        await callback.answer()
        return

    clients = await clientService.getAllClients()

    if not clients:
        await callback.message.answer("Клиенты не найдены")
        await callback.answer()
        return

    header = "Клиенты:\n\n Id | Full Name | US State | Language | Status\n"
    parts = [header]
    current = header

    for i, client in enumerate(clients, start=1):
        line = (
            f"{i}. {client['full_name']} | "
            f"{client['us_state']} | "
            f"{client['language']} | "
            f"{client['status']}\n"
        )

        if len(current) + len(line) > MAX_MESSAGE_LEN:
            parts.append(current)
            current = line
        else:
            current += line

    if current and (len(parts) == 1 or current != header):
        parts.append(current)

    for chunk in parts[1:]:
        await callback.message.answer(chunk)
    await callback.answer()
