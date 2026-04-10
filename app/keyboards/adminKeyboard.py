from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

adminKeyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Send Message", callback_data="admin_send")],
        [InlineKeyboardButton(text="Create Client", callback_data="admin_create_client")],
        [InlineKeyboardButton(text="Clients List", callback_data="admin_clients")],
    ]
)
