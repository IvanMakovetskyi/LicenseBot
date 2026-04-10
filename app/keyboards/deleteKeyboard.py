from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def getDeleteClientsKeyboard(clients):
    keyboard = []

    for client in clients:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{client['full_name']} | {client['us_state']} | {client['status']}",
                callback_data=f"delete_client_select:{client['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="Отмена",
            callback_data="delete_client_cancel"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def getDeleteConfirmKeyboard(clientId: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=f"delete_client_confirm:{clientId}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="delete_client_cancel"
                )
            ]
        ]
    )
