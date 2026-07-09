from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.messageService import CATEGORIES, CLIENT_STATES, EDITABLE_STATES, LANGUAGES


def messageMenuKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Список сообщений", callback_data="ma:list")
    builder.button(text="✏️ Редактировать сообщение", callback_data="ma:edit")
    builder.button(text="➕ Добавить сообщение", callback_data="ma:add")
    builder.button(text="🏳️ Создать override для штата", callback_data="ma:override")
    builder.button(text="🔀 Вкл/выкл сообщение", callback_data="ma:toggle")
    builder.button(text="🧩 Управление flow", callback_data="ma:flow")
    builder.button(text="🔍 Проверить сообщения", callback_data="ma:audit")
    builder.button(text="⬅️ Назад в админ панель", callback_data="ma:back")
    builder.adjust(1)
    return builder.as_markup()


def keysKeyboard(keys: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in keys:
        builder.button(text=key, callback_data=f"ma:key:{key}")
    builder.button(text="⬅️ Назад", callback_data="ma:menu")
    builder.adjust(1)
    return builder.as_markup()


def statesKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for state in EDITABLE_STATES:
        builder.button(text=state, callback_data=f"ma:st:{state}")
    builder.button(text="⬅️ Назад", callback_data="ma:menu")
    builder.adjust(3)
    return builder.as_markup()


def languagesKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lang in LANGUAGES:
        builder.button(text=lang, callback_data=f"ma:lang:{lang}")
    builder.button(text="⬅️ Назад", callback_data="ma:menu")
    builder.adjust(2)
    return builder.as_markup()


def editorKeyboard(isActive: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить label", callback_data="ma:e:label")
    builder.button(text="📝 Изменить текст", callback_data="ma:e:text")
    builder.button(text="🧩 Изменить placeholders", callback_data="ma:e:ph")
    toggleText = "🚫 Деактивировать" if isActive else "✅ Активировать"
    builder.button(text=toggleText, callback_data="ma:e:toggle")
    builder.button(text="👁 Предпросмотр", callback_data="ma:e:preview")
    builder.button(text="💾 Сохранить", callback_data="ma:e:save")
    builder.button(text="⬅️ В меню сообщений", callback_data="ma:menu")
    builder.adjust(1)
    return builder.as_markup()


# --------------------------------------------------------------------------- #
# Flow management
# --------------------------------------------------------------------------- #
def flowStatesKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for state in CLIENT_STATES:
        builder.button(text=state, callback_data=f"ma:fst:{state}")
    builder.button(text="⬅️ Назад", callback_data="ma:menu")
    builder.adjust(3)
    return builder.as_markup()


def flowMenuKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить ключ", callback_data="ma:f:add")
    builder.button(text="➖ Удалить ключ", callback_data="ma:f:del")
    builder.button(text="🔢 Изменить порядок", callback_data="ma:f:order")
    builder.button(text="🏷 Изменить категорию", callback_data="ma:f:cat")
    builder.button(text="⬅️ К выбору штата", callback_data="ma:flow")
    builder.adjust(1)
    return builder.as_markup()


def flowKeysKeyboard(keys: list[str], backTo: str = "ma:f:back") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in keys:
        builder.button(text=key, callback_data=f"ma:fk:{key}")
    builder.button(text="⬅️ Назад", callback_data=backTo)
    builder.adjust(1)
    return builder.as_markup()


def flowCategoryKeyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in CATEGORIES:
        builder.button(text=category, callback_data=f"ma:fcat:{category}")
    builder.button(text="⬅️ Назад", callback_data="ma:f:back")
    builder.adjust(2)
    return builder.as_markup()
