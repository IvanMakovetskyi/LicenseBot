from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import settings

from states.adminSendState import AdminSendState
from keyboards.sendKeyboard import (
    clientKeyboard,
    messageKeyboard,
    confirmKeyboard,
)
from services.sendService import resolveMessage, getAvailableMessages
from services.clientService import clientService


router = Router()


def isAdmin(userId: int) -> bool:
    return userId in settings.ADMINS


async def openSendInterface(
    message: Message,
    state: FSMContext,
    userId: int,
):
    if not isAdmin(userId):
        return

    if message.chat.type != "private":
        await message.answer("Use /send in private chat with the bot.")
        return

    clients = await clientService.getAllClients()

    if not clients:
        await message.answer("No clients found.")
        return

    await state.clear()
    await state.set_state(AdminSendState.choosingClient)

    await message.answer(
        "Choose client:",
        reply_markup=clientKeyboard(clients),
    )


@router.message(Command("send"))
async def sendCommand(message: Message, state: FSMContext):
    if not message.from_user:
        return

    await openSendInterface(
        message=message,
        state=state,
        userId=message.from_user.id,
    )


@router.callback_query(F.data == "admin_send")
async def adminSend(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    if callback.message.chat.type == "private":
        await openSendInterface(
            message=callback.message,
            state=state,
            userId=callback.from_user.id,
        )
        await callback.answer()
        return

    client = await clientService.getClientByChatId(callback.message.chat.id)

    if not client:
        await callback.message.answer("Client is not created yet.")
        await callback.answer()
        return

    await state.clear()
    await state.update_data(
        clientId=client["id"],
        clientName=client["full_name"],
        clientChatId=client["chat_id"],
        stateCode=client["us_state"],
    )

    messageKeys = getAvailableMessages(client["us_state"])

    await state.set_state(AdminSendState.choosingMessage)

    await callback.message.answer(
        f"Client: {client['full_name']}\n"
        f"State: {client['us_state']}\n\n"
        f"Choose message:",
        reply_markup=messageKeyboard(messageKeys),
    )

    await callback.answer()


@router.callback_query(
    AdminSendState.choosingClient,
    F.data.startswith("send_client:")
)
async def chooseClient(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    clientId = int(callback.data.split(":")[1])
    client = await clientService.getClientById(clientId)

    if not client:
        await callback.answer("Client not found.", show_alert=True)
        return

    await state.update_data(
        clientId=client["id"],
        clientName=client["full_name"],
        clientChatId=client["chat_id"],
        stateCode=client["us_state"],
    )

    messageKeys = getAvailableMessages(client["us_state"])

    await state.set_state(AdminSendState.choosingMessage)

    await callback.message.edit_text(
        f"Client: {client['full_name']}\n"
        f"State: {client['us_state']}\n\n"
        f"Choose message:",
        reply_markup=messageKeyboard(messageKeys),
    )
    await callback.answer()


@router.callback_query(
    AdminSendState.choosingMessage,
    F.data.startswith("send_message:")
)
async def chooseMessage(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    data = await state.get_data()
    stateCode = data.get("stateCode")

    if not stateCode:
        await callback.answer("State is missing.", show_alert=True)
        return

    messageKey = callback.data.split(":")[1]
    template = resolveMessage(messageKey, stateCode)

    text = template["text"]
    placeholders = template.get("placeholders", [])

    await state.update_data(
        messageKey=messageKey,
        templateText=text,
        placeholders=placeholders,
        placeholderIndex=0,
        values={},
    )

    if placeholders:
        await state.set_state(AdminSendState.fillingPlaceholder)
        await callback.message.edit_text(
            f"Enter value for: {placeholders[0]}"
        )
    else:
        await state.update_data(finalText=text)
        await state.set_state(AdminSendState.confirming)

        await callback.message.edit_text(
            f"Preview:\n\n{text}",
            reply_markup=confirmKeyboard(),
        )

    await callback.answer()


@router.message(AdminSendState.fillingPlaceholder)
async def fillPlaceholder(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return

    data = await state.get_data()

    placeholders = data.get("placeholders", [])
    index = data.get("placeholderIndex", 0)
    values = data.get("values", {})

    if index >= len(placeholders):
        await message.answer("Unexpected state. Start again with /send.")
        await state.clear()
        return

    currentPlaceholder = placeholders[index]
    values[currentPlaceholder] = message.text.strip() if message.text else ""

    index += 1

    if index < len(placeholders):
        await state.update_data(
            values=values,
            placeholderIndex=index,
        )
        await message.answer(f"Enter value for: {placeholders[index]}")
        return

    templateText = data["templateText"]

    try:
        finalText = templateText.format(**values)
    except KeyError as error:
        await message.answer(f"Missing placeholder value: {error}")
        await state.clear()
        return

    await state.update_data(
        values=values,
        finalText=finalText,
    )
    await state.set_state(AdminSendState.confirming)

    await message.answer(
        f"Preview:\n\n{finalText}",
        reply_markup=confirmKeyboard(),
    )


@router.callback_query(
    AdminSendState.confirming,
    F.data == "send_confirm"
)
async def confirmSend(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    data = await state.get_data()

    clientId = data.get("clientId")
    clientChatId = data.get("clientChatId")
    finalText = data.get("finalText")
    clientName = data.get("clientName", "Unknown client")
    messageKey = data.get("messageKey")

    if not clientChatId or not finalText:
        await callback.answer("Missing data for sending.", show_alert=True)
        await state.clear()
        return

    await bot.send_message(chat_id=clientChatId, text=finalText)

    if messageKey == "payment":
        await clientService.updateStatus(clientId, "in_progress")

    if messageKey == "congratulations":
        await clientService.updateStatus(clientId, "done")

    await callback.message.edit_text(
        f"Message sent to {clientName} ✅"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "send_cancel")
async def cancelSend(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or not isAdmin(callback.from_user.id):
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text("Sending canceled.")
    await callback.answer()
