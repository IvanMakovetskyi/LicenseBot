from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

adminKeyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Send Greeting", callback_data="send_greeting")]
    ]
)
