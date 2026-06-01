from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def clientKeyboard(clients) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for client in clients:
        builder.button(
            text=f'{client["full_name"]} ({client["us_state"]})',
            callback_data=f'send_client:{client["id"]}',
        )

    builder.adjust(1)
    return builder.as_markup()

def messageKeyboard(messages: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for item in messages:
        label = item["label"]
        if item.get("is_last"):
            label = f"{label} (last)"

        builder.button(
            text=label,
            callback_data=f"send_message:{item['key']}"
        )

    builder.adjust(1)
    return builder.as_markup()

def confirmKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отправить", callback_data="send_confirm")
    builder.button(text="Отмена", callback_data="send_cancel")
    builder.adjust(2)
    return builder.as_markup()
