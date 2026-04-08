from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

mainKeyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Status")],
        [KeyboardButton(text="Upload document")]
    ],
    resize_keyboard=True
)
