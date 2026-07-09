from aiogram.fsm.state import State, StatesGroup


class MessageAdminState(StatesGroup):
    # Template editor selection + editing
    pickingKey = State()
    enteringNewKey = State()
    pickingState = State()
    pickingLang = State()
    editorMenu = State()
    editingLabel = State()
    editingText = State()
    editingPlaceholders = State()

    # Flow management
    flowMenu = State()
    flowPickAddKey = State()
    flowPickRemoveKey = State()
    flowPickOrderKey = State()
    flowEnteringOrder = State()
    flowPickCategoryKey = State()
    flowPickCategoryValue = State()
