from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.clientService import clientService
from keyboards.deleteKeyboard import (
    getDeleteClientsKeyboard,
    getDeleteConfirmKeyboard
)
from config import settings

router = Router()


@router.callback_query(F.data == "admin_delete_client")
async def showDeleteClients(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMINS:
        await callback.answer("У вас нет админ прав", show_alert=True)
        return

    clients = await clientService.getAllClients()

    if not clients:
        await callback.message.answer("Клиенты не найдены")
        await callback.answer()
        return

    await callback.message.answer(
        "Выберите клиента для удаления:",
        reply_markup=getDeleteClientsKeyboard(clients)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_client_select:"))
async def selectDeleteClient(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMINS:
        await callback.answer("У вас нет админ прав", show_alert=True)
        return

    clientId = int(callback.data.split(":")[1])
    client = await clientService.getClientById(clientId)

    if not client:
        await callback.message.answer("Клиент не найден")
        await callback.answer()
        return

    text = (
        "Вы уверены, что хотите удалить клиента?\n\n"
        f"Имя: {client['full_name']}\n"
        f"Штат: {client['us_state']}\n"
        f"Статус: {client['status']}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=getDeleteConfirmKeyboard(clientId)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_client_confirm:"))
async def confirmDeleteClient(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMINS:
        await callback.answer("У вас нет админ прав", show_alert=True)
        return

    clientId = int(callback.data.split(":")[1])
    client = await clientService.getClientById(clientId)

    if not client:
        await callback.message.edit_text("Клиент уже удалён или не найден")
        await callback.answer()
        return

    await clientService.deleteClient(clientId)

    await callback.message.edit_text("Клиент успешно удалён")
    await callback.answer()


@router.callback_query(F.data == "delete_client_cancel")
async def cancelDeleteClient(callback: CallbackQuery):
    if callback.from_user.id not in settings.ADMINS:
        await callback.answer("У вас нет админ прав", show_alert=True)
        return

    await callback.message.edit_text("Удаление отменено")
    await callback.answer()
