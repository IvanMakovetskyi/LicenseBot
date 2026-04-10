from aiogram.fsm.state import State, StatesGroup

class CreateClientState(StatesGroup):
    waitingFullName = State()
    waitingUsState = State()
