from aiogram.fsm.state import State, StatesGroup

class Login(StatesGroup):
    two_factor_auth = State()