from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from services.clientService import clientService
from states.createClientState import CreateClientState
from config import settings

router = Router()

def isAdmin(userId: int) -> bool:
    return userId in settings.ADMINS

@router.callback_query(F.data == "admin_create_client")
async def adminCreateClient(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    if callback.message.chat.type == "private":
        await callback.message.answer("Откройте админ панель в чате с клиентом")
        await callback.answer()
        return
    
    chatId = callback.message.chat.id

    existingClient = await clientService.getClientByChatId(chatId)

    if existingClient:
        await callback.message.answer(
            f"Клиент уже есть в базе:\n\n"
            f"{existingClient['full_name']}\n"
            f"Штат: {existingClient['us_state']}\n"
            f"Статус: {existingClient['status']}"
        )
        await callback.answer()
        return

    await state.clear()
    await state.update_data(chatId=callback.message.chat.id)
    await state.set_state(CreateClientState.waitingFullName)

    await callback.message.answer("Введите полное имя клиента:")
    await callback.answer()

@router.message(CreateClientState.waitingFullName)
async def getFullName(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return

    await state.update_data(fullName=message.text.strip())
    await state.set_state(CreateClientState.waitingUsState)
    await message.answer("Введите штат (CA, FL, NY, PA):")


@router.message(CreateClientState.waitingUsState)
async def getUsState(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return

    usState = message.text.strip().upper()
    allowedStates = {"CA", "FL", "NY", "PA"}

    if usState not in allowedStates:
        await message.answer("Неверный штат. ВВедите: CA, FL, NY, или PA.")
        return

    data = await state.get_data()
    chatId = data["chatId"]
    fullName = data["fullName"]

    await clientService.createClient(
        chatId=chatId,
        fullName=fullName,
        usState=usState,
        status="new",
    )

    await message.answer(
        f"Клиент создан:\n\n"
        f"{fullName}\n"
        f"Штат: {usState}"
    )

    await state.clear()
