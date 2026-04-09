from aiogram.fsm.state import State, StatesGroup

class AdminSendState(StatesGroup):
    choosingClient = State()
    choosingMessage = State()
    fillingPlaceholder  = State()
    confirming = State()
