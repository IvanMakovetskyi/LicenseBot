from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from keyboards.adminKeyboard import adminKeyboard
from keyboards.messageAdminKeyboard import (
    editorKeyboard,
    flowCategoryKeyboard,
    flowKeysKeyboard,
    flowMenuKeyboard,
    flowStatesKeyboard,
    keysKeyboard,
    languagesKeyboard,
    messageMenuKeyboard,
    statesKeyboard,
)
from services import messageService
from states.messageAdminState import MessageAdminState

router = Router()

MAX_MESSAGE_LEN = 4000
_EDITOR_TEXT_PREVIEW = 800


def isAdmin(userId: int) -> bool:
    return userId in settings.ADMINS


def _guard(callback: CallbackQuery) -> bool:
    return bool(callback.from_user and isAdmin(callback.from_user.id) and callback.message)


async def _sendChunks(message: Message, header: str, lines: list[str]) -> None:
    """Send a long list split into <= MAX_MESSAGE_LEN chunks."""
    current = header
    for line in lines:
        candidate = f"{line}\n"
        if len(current) + len(candidate) > MAX_MESSAGE_LEN:
            await message.answer(current)
            current = candidate
        else:
            current += candidate
    if current.strip():
        await message.answer(current)


# --------------------------------------------------------------------------- #
# Menu entry
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "admin_messages")
async def openMessageMenu(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer("У вас нет админ прав", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("📨 Управление сообщениями:", reply_markup=messageMenuKeyboard())
    await callback.answer()


@router.callback_query(F.data == "ma:menu")
async def backToMenu(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(None)
    await callback.message.edit_text("📨 Управление сообщениями:", reply_markup=messageMenuKeyboard())
    await callback.answer()


@router.callback_query(F.data == "ma:back")
async def backToAdmin(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.clear()
    envLabel = " (DEV mode)" if settings.APP_ENV == "dev" else ""
    await callback.message.edit_text(f"Админ панель:{envLabel}", reply_markup=adminKeyboard)
    await callback.answer()


# --------------------------------------------------------------------------- #
# List
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "ma:list")
async def listMessages(callback: CallbackQuery):
    if not _guard(callback):
        await callback.answer()
        return

    templates = await messageService.listTemplates()
    if not templates:
        await callback.message.answer("Шаблоны не найдены.")
        await callback.answer()
        return

    lines = []
    for tpl in templates:
        flag = "✅" if tpl["is_active"] else "🚫"
        lines.append(
            f"{flag} {tpl['message_key']} | {tpl['state_code']} | {tpl['language']} | {tpl['label']}"
        )
    await _sendChunks(callback.message, "📄 Шаблоны сообщений:\n", lines)
    await callback.answer()


# --------------------------------------------------------------------------- #
# Selection flow (edit / override / toggle / add)
# --------------------------------------------------------------------------- #
@router.callback_query(F.data.in_({"ma:edit", "ma:override", "ma:toggle"}))
async def startSelection(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return

    mode = callback.data.split(":")[1]
    keys = await messageService.listMessageKeys()
    if not keys:
        await callback.message.answer("В базе нет ни одного шаблона. Используйте «Добавить сообщение».")
        await callback.answer()
        return

    await state.set_state(MessageAdminState.pickingKey)
    await state.update_data(mode=mode)
    await callback.message.edit_text("Выберите ключ сообщения:", reply_markup=keysKeyboard(keys))
    await callback.answer()


@router.callback_query(F.data == "ma:add")
async def startAdd(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(MessageAdminState.enteringNewKey)
    await state.update_data(mode="add")
    await callback.message.edit_text(
        "Введите message_key нового сообщения (латиница, snake_case), например: welcome"
    )
    await callback.answer()


@router.message(MessageAdminState.enteringNewKey)
async def receiveNewKey(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    key = (message.text or "").strip()
    if not key or " " in key:
        await message.answer("Ключ не должен быть пустым и не может содержать пробелы. Попробуйте снова.")
        return
    await state.update_data(msgKey=key)
    await state.set_state(MessageAdminState.pickingState)
    await message.answer(f"Ключ: {key}\nВыберите штат:", reply_markup=statesKeyboard())


@router.callback_query(MessageAdminState.pickingKey, F.data.startswith("ma:key:"))
async def pickKey(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    key = callback.data.split(":", 2)[2]
    await state.update_data(msgKey=key)
    await state.set_state(MessageAdminState.pickingState)
    await callback.message.edit_text(f"Ключ: {key}\nВыберите штат:", reply_markup=statesKeyboard())
    await callback.answer()


@router.callback_query(MessageAdminState.pickingState, F.data.startswith("ma:st:"))
async def pickState(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    stateCode = callback.data.split(":", 2)[2]
    await state.update_data(msgState=stateCode)
    await state.set_state(MessageAdminState.pickingLang)
    data = await state.get_data()
    await callback.message.edit_text(
        f"Ключ: {data['msgKey']}\nШтат: {stateCode}\nВыберите язык:",
        reply_markup=languagesKeyboard(),
    )
    await callback.answer()


@router.callback_query(MessageAdminState.pickingLang, F.data.startswith("ma:lang:"))
async def pickLang(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    language = callback.data.split(":", 2)[2]
    data = await state.get_data()
    key = data["msgKey"]
    stateCode = data["msgState"]

    existing = await messageService.getTemplate(key, stateCode, language)
    if existing:
        buffer = {
            "exists": True,
            "bufLabel": existing["label"],
            "bufText": existing["text"],
            "bufPlaceholders": existing["placeholders"],
            "bufActive": existing["is_active"],
            "bufCategory": existing.get("message_category", "workflow"),
            "bufOrder": existing.get("display_order", 0),
        }
    else:
        buffer = {
            "exists": False,
            "bufLabel": "",
            "bufText": "",
            "bufPlaceholders": [],
            "bufActive": True,
            "bufCategory": "workflow",
            "bufOrder": 0,
        }

    await state.update_data(msgLang=language, **buffer)
    await state.set_state(MessageAdminState.editorMenu)
    await _renderEditor(callback, state)
    await callback.answer()


# --------------------------------------------------------------------------- #
# Editor
# --------------------------------------------------------------------------- #
def _editorText(data: dict) -> str:
    text = data.get("bufText", "") or ""
    preview = text if len(text) <= _EDITOR_TEXT_PREVIEW else text[:_EDITOR_TEXT_PREVIEW] + " …"
    placeholders = data.get("bufPlaceholders", [])
    status = "✅ активен" if data.get("bufActive", True) else "🚫 выключен"
    existsNote = (
        "" if data.get("exists") else "\n⚠️ Шаблон ещё не создан — заполните и нажмите «Сохранить»."
    )
    return (
        "🛠 Редактор шаблона\n\n"
        f"Ключ: {data['msgKey']}\n"
        f"Штат: {data['msgState']}\n"
        f"Язык: {data['msgLang']}\n"
        f"Статус: {status}\n"
        f"Label: {data.get('bufLabel') or '—'}\n"
        f"Placeholders: {', '.join(placeholders) if placeholders else '—'}"
        f"{existsNote}\n\n"
        f"Текст:\n{preview or '—'}\n\n"
        "После правки текста/label/placeholders нажмите «Сохранить»."
    )


async def _renderEditor(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await callback.message.edit_text(
        _editorText(data),
        reply_markup=editorKeyboard(data.get("bufActive", True)),
    )


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:label")
async def editLabel(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(MessageAdminState.editingLabel)
    await callback.message.answer("Отправьте новый label:")
    await callback.answer()


@router.message(MessageAdminState.editingLabel)
async def receiveLabel(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    if not message.text:
        await message.answer("Отправьте label текстом.")
        return
    await state.update_data(bufLabel=message.text.strip())
    await state.set_state(MessageAdminState.editorMenu)
    data = await state.get_data()
    await message.answer(_editorText(data), reply_markup=editorKeyboard(data.get("bufActive", True)))


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:text")
async def editText(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(MessageAdminState.editingText)
    await callback.message.answer(
        "Отправьте новый текст сообщения.\nМожно многострочный, с плейсхолдерами вида {amount}."
    )
    await callback.answer()


@router.message(MessageAdminState.editingText)
async def receiveText(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    # Preserve multiline formatting exactly as sent.
    if message.text is None:
        await message.answer("Отправьте текст сообщения.")
        return
    await state.update_data(bufText=message.text)
    await state.set_state(MessageAdminState.editorMenu)
    data = await state.get_data()
    await message.answer(_editorText(data), reply_markup=editorKeyboard(data.get("bufActive", True)))


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:ph")
async def editPlaceholders(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(MessageAdminState.editingPlaceholders)
    await callback.message.answer(
        "Отправьте плейсхолдеры через запятую, например:\namount, login, password\n"
        "Или JSON-массив: [\"amount\", \"login\"]\nПустой список — отправьте «-»."
    )
    await callback.answer()


@router.message(MessageAdminState.editingPlaceholders)
async def receivePlaceholders(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    try:
        placeholders = messageService.parsePlaceholders(message.text or "")
    except ValueError:
        await message.answer("Некорректный формат. Проверьте JSON или список через запятую и попробуйте снова.")
        return
    await state.update_data(bufPlaceholders=placeholders)
    await state.set_state(MessageAdminState.editorMenu)
    data = await state.get_data()
    await message.answer(_editorText(data), reply_markup=editorKeyboard(data.get("bufActive", True)))


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:toggle")
async def toggleActive(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    newActive = not data.get("bufActive", True)
    await state.update_data(bufActive=newActive)

    # If the row already exists, persist the toggle immediately.
    if data.get("exists"):
        await messageService.setTemplateActive(
            data["msgKey"], data["msgState"], data["msgLang"], newActive
        )
        await callback.answer("Статус обновлён")
    else:
        await callback.answer("Статус изменён (сохранится при создании)")
    await _renderEditor(callback, state)


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:preview")
async def previewTemplate(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    text = data.get("bufText", "") or "(пусто)"
    placeholders = data.get("bufPlaceholders", [])
    note = f"\n\nПлейсхолдеры: {', '.join(placeholders)}" if placeholders else ""
    await callback.message.answer(f"👁 Предпросмотр:\n\n{text}{note}")
    await callback.answer()


@router.callback_query(MessageAdminState.editorMenu, F.data == "ma:e:save")
async def saveTemplate(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()

    if not (data.get("bufText") or "").strip():
        await callback.answer("Нельзя сохранить пустой текст.", show_alert=True)
        return
    if not (data.get("bufLabel") or "").strip():
        await callback.answer("Заполните label перед сохранением.", show_alert=True)
        return

    await messageService.saveTemplate(
        messageKey=data["msgKey"],
        stateCode=data["msgState"],
        language=data["msgLang"],
        label=data["bufLabel"],
        text=data["bufText"],
        placeholders=data.get("bufPlaceholders", []),
        messageCategory=data.get("bufCategory", "workflow"),
        displayOrder=data.get("bufOrder", 0),
        isActive=data.get("bufActive", True),
    )
    await state.update_data(exists=True)
    await callback.answer("Сохранено ✅")
    await callback.message.edit_text(
        f"✅ Шаблон сохранён:\n{data['msgKey']} | {data['msgState']} | {data['msgLang']}",
        reply_markup=messageMenuKeyboard(),
    )
    await state.set_state(None)


# --------------------------------------------------------------------------- #
# Flow management
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == "ma:flow")
async def flowChooseState(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    await state.set_state(None)
    await callback.message.edit_text("Выберите штат для управления flow:", reply_markup=flowStatesKeyboard())
    await callback.answer()


async def _renderFlow(callback: CallbackQuery, usState: str) -> None:
    flows = await messageService.getFlows(usState)
    if flows:
        lines = "\n".join(
            f"{f['display_order']}. {'✅' if f['is_active'] else '🚫'} {f['message_key']} ({f['message_category']})"
            for f in flows
        )
    else:
        lines = "(пусто)"
    await callback.message.edit_text(
        f"🧩 Flow для {usState}:\n\n{lines}",
        reply_markup=flowMenuKeyboard(),
    )


@router.callback_query(F.data.startswith("ma:fst:"))
async def flowState(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    usState = callback.data.split(":", 2)[2]
    await state.set_state(MessageAdminState.flowMenu)
    await state.update_data(flowState=usState)
    await _renderFlow(callback, usState)
    await callback.answer()


@router.callback_query(F.data == "ma:f:back")
async def flowBack(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    usState = data.get("flowState")
    if not usState:
        await flowChooseState(callback, state)
        return
    await state.set_state(MessageAdminState.flowMenu)
    await _renderFlow(callback, usState)
    await callback.answer()


@router.callback_query(F.data == "ma:f:add")
async def flowAddStart(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    usState = data.get("flowState")
    allKeys = await messageService.listMessageKeys()
    flows = await messageService.getFlows(usState)
    existing = {f["message_key"] for f in flows}
    candidates = [k for k in allKeys if k not in existing]

    if not candidates:
        await callback.answer("Все ключи уже добавлены в этот flow.", show_alert=True)
        return

    await state.set_state(MessageAdminState.flowPickAddKey)
    await callback.message.edit_text(
        f"Добавить ключ в flow {usState}:", reply_markup=flowKeysKeyboard(candidates)
    )
    await callback.answer()


@router.callback_query(MessageAdminState.flowPickAddKey, F.data.startswith("ma:fk:"))
async def flowAddKey(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    key = callback.data.split(":", 2)[2]
    data = await state.get_data()
    usState = data["flowState"]
    await messageService.addFlowKey(usState, key)
    await state.set_state(MessageAdminState.flowMenu)
    await _renderFlow(callback, usState)
    await callback.answer("Ключ добавлен")


@router.callback_query(F.data == "ma:f:del")
async def flowRemoveStart(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    usState = data.get("flowState")
    flows = await messageService.getFlows(usState)
    keys = [f["message_key"] for f in flows]
    if not keys:
        await callback.answer("Flow пуст.", show_alert=True)
        return
    await state.set_state(MessageAdminState.flowPickRemoveKey)
    await callback.message.edit_text(
        f"Удалить ключ из flow {usState}:", reply_markup=flowKeysKeyboard(keys)
    )
    await callback.answer()


@router.callback_query(MessageAdminState.flowPickRemoveKey, F.data.startswith("ma:fk:"))
async def flowRemoveKey(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    key = callback.data.split(":", 2)[2]
    data = await state.get_data()
    usState = data["flowState"]
    await messageService.removeFlowKey(usState, key)
    await state.set_state(MessageAdminState.flowMenu)
    await _renderFlow(callback, usState)
    await callback.answer("Ключ удалён")


@router.callback_query(F.data == "ma:f:order")
async def flowOrderStart(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    usState = data.get("flowState")
    flows = await messageService.getFlows(usState)
    keys = [f["message_key"] for f in flows]
    if not keys:
        await callback.answer("Flow пуст.", show_alert=True)
        return
    await state.set_state(MessageAdminState.flowPickOrderKey)
    await callback.message.edit_text(
        f"Выберите ключ для изменения порядка в flow {usState}:",
        reply_markup=flowKeysKeyboard(keys),
    )
    await callback.answer()


@router.callback_query(MessageAdminState.flowPickOrderKey, F.data.startswith("ma:fk:"))
async def flowOrderPickKey(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    key = callback.data.split(":", 2)[2]
    await state.update_data(flowOrderKey=key)
    await state.set_state(MessageAdminState.flowEnteringOrder)
    await callback.message.answer(f"Введите новый порядок (число) для «{key}»:")
    await callback.answer()


@router.message(MessageAdminState.flowEnteringOrder)
async def flowSetOrder(message: Message, state: FSMContext):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    if not raw.lstrip("-").isdigit():
        await message.answer("Введите целое число.")
        return
    data = await state.get_data()
    usState = data["flowState"]
    key = data["flowOrderKey"]
    await messageService.setFlowOrder(usState, key, int(raw))

    flows = await messageService.getFlows(usState)
    lines = "\n".join(
        f"{f['display_order']}. {'✅' if f['is_active'] else '🚫'} {f['message_key']} ({f['message_category']})"
        for f in flows
    ) or "(пусто)"
    await state.set_state(MessageAdminState.flowMenu)
    await message.answer(f"🧩 Flow для {usState}:\n\n{lines}", reply_markup=flowMenuKeyboard())


@router.callback_query(F.data == "ma:f:cat")
async def flowCategoryStart(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    data = await state.get_data()
    usState = data.get("flowState")
    flows = await messageService.getFlows(usState)
    keys = [f["message_key"] for f in flows]
    if not keys:
        await callback.answer("Flow пуст.", show_alert=True)
        return
    await state.set_state(MessageAdminState.flowPickCategoryKey)
    await callback.message.edit_text(
        f"Выберите ключ для изменения категории в flow {usState}:",
        reply_markup=flowKeysKeyboard(keys),
    )
    await callback.answer()


@router.callback_query(MessageAdminState.flowPickCategoryKey, F.data.startswith("ma:fk:"))
async def flowCategoryPickKey(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    key = callback.data.split(":", 2)[2]
    await state.update_data(flowCatKey=key)
    await state.set_state(MessageAdminState.flowPickCategoryValue)
    await callback.message.edit_text(
        f"Выберите категорию для «{key}»:", reply_markup=flowCategoryKeyboard()
    )
    await callback.answer()


@router.callback_query(MessageAdminState.flowPickCategoryValue, F.data.startswith("ma:fcat:"))
async def flowCategorySet(callback: CallbackQuery, state: FSMContext):
    if not _guard(callback):
        await callback.answer()
        return
    category = callback.data.split(":", 2)[2]
    data = await state.get_data()
    usState = data["flowState"]
    key = data["flowCatKey"]
    await messageService.setFlowCategory(usState, key, category)
    await state.set_state(MessageAdminState.flowMenu)
    await _renderFlow(callback, usState)
    await callback.answer("Категория обновлена")


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
async def _runAndSendAudit(message: Message) -> None:
    report = await messageService.runAudit()
    text = messageService.formatAuditReport(report)
    lines = text.split("\n")
    await _sendChunks(message, "", lines)


@router.callback_query(F.data == "ma:audit")
async def auditButton(callback: CallbackQuery):
    if not _guard(callback):
        await callback.answer()
        return
    await _runAndSendAudit(callback.message)
    await callback.answer()


@router.message(Command("message_audit"))
async def auditCommand(message: Message):
    if not message.from_user or not isAdmin(message.from_user.id):
        return
    await _runAndSendAudit(message)
