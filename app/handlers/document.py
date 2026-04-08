import os
from aiogram import Bot, Router, F
from aiogram.types import Message

router = Router()

@router.message(F.document)
async def documentHandler(message: Message, bot: Bot):
    document = message.document

    os.makedirs("./documents", exist_ok=True)

    file_id = document.file_id
    file_name = document.file_name

    await message.answer(f"Recieved file: {file_name}")

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    destination = f"./documents/{file_name}"
    await bot.download_file(file_path, destination=destination)

    await message.answer("Document saved successfully.")
