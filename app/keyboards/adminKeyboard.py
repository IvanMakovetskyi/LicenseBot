from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

adminKeyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отправить сообщение", callback_data="admin_send")],
        [InlineKeyboardButton(text="Добавить клиента", callback_data="admin_create_client")],
        [InlineKeyboardButton(text="Список клиентов", callback_data="admin_clients")],
    ]
)
