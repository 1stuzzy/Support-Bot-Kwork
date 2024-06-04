from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    phone_number = State()
    full_name = State()


class CommentState(StatesGroup):
    text = State()


class MessageState(StatesGroup):
    text = State()
    confirming_text = State()


class ChangeReward(StatesGroup):
    type = State()
    amount = State()
