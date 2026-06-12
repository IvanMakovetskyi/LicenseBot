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

<<<<<<< HEAD
<<<<<<< Updated upstream
    for key in messageKeys:
        builder.button(
            text=getMessageLabel(key),
            callback_data=f"send_message:{key}"
=======
    for item in messages:
        label = item.get("label") or item.get("key") or "Unnamed message"
        if item.get("is_last"):
            label = f"{label} (last)"

        builder.button(
            text=str(label),
            callback_data=f"send_message:{item['key']}"
>>>>>>> Stashed changes
=======
    for item in messages:
        label = item["label"]
        if item.get("is_last"):
            label = f"{label} (last)"

        builder.button(
            text=label,
            callback_data=f"send_message:{item['key']}"
>>>>>>> ef8d7bc7d9263464bfcd592445306b2db6fd68bc
        )

    builder.adjust(1)
    return builder.as_markup()

def confirmKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отправить", callback_data="send_confirm")
    builder.button(text="Отмена", callback_data="send_cancel")
    builder.adjust(2)
    return builder.as_markup()
