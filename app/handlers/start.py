from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from repositories.caseRepository import getCase, createCase

router = Router()

@router.message(Command("start"))
async def startHandler(message: Message):
    chatId = message.chat.id

    case = getCase(chatId)

    if case is None:
        createCase(chatId, "CA", "new")
        await message.answer("Case created.")
    else:
        await message.answer("Case already exists.")
