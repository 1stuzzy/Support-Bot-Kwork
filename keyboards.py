from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from loader import db
import logging


def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📱 Отправить номер телефона", request_contact=True))
    return keyboard


def main_menu(user_id):
    from functions import is_agent, is_admin
    keyboard = InlineKeyboardMarkup()
    if is_agent(user_id):
        keyboard.add(InlineKeyboardButton('🔎 Найти по имени', switch_inline_query_current_chat='name='))
    elif is_admin(user_id):
        keyboard.add(InlineKeyboardButton('🔎 Найти по имени', switch_inline_query_current_chat='user='))
        keyboard.add(InlineKeyboardButton('💸 Изменить вознаграждение', callback_data='select_reward'))
    else:
        keyboard.add(InlineKeyboardButton("ℹ️ Бонусная программа", callback_data='menu_info'))
        keyboard.add(InlineKeyboardButton("ℹ️ Информация", callback_data='menu_info'))
    return keyboard


async def get_key(user_id):
    from functions import is_agent, is_admin
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if is_agent(user_id):
        keyboard.add('Меню агента 🖥')
        keyboard.add('Настройки ⚙️', 'Информация ℹ️')
    elif is_admin(user_id):
        keyboard.add('Меню администратора 👨‍💻')
        keyboard.add('Настройки ⚙️', 'Информация ℹ️')
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('Информация ℹ️')
        keyboard.add('Техническая поддержка 👨‍💻')
    return keyboard


async def search_menu(user_id, element_id):
    from functions import get_user_group, is_admin, is_agent
    keyboard = InlineKeyboardMarkup()

    group = get_user_group(element_id)
    comment = db.get_comment(element_id)

    if is_admin(user_id):
        keyboard.add(InlineKeyboardButton("✉️ Отправить сообщение", callback_data=f"send_message={element_id}"))
        keyboard.add(InlineKeyboardButton(f"{'🪪 Назначить агентом' if group == 'Реферал' else '💤 Разжаловать агента'}",
                                          callback_data=f"set_group={element_id}"))
        if not is_agent(element_id):
            keyboard.add(InlineKeyboardButton("🔹 Изменить статус", callback_data=f"choose_status={element_id}"))
        keyboard.add(InlineKeyboardButton("🔃 Обновить", callback_data=f"i={element_id}"))

    elif is_agent(user_id):
        keyboard.add(InlineKeyboardButton(
            f"{'💬 Добавить задачу' if comment == '' else '✍️ Изменить задачу'}",
            callback_data=f"set_comment={element_id}"
        ))
        keyboard.add(InlineKeyboardButton("🔃 Обновить", callback_data=f"i={element_id}"))

    return keyboard


def status_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("В обработке ⏳", callback_data=f"status_waiting={user_id}"))
    keyboard.add(InlineKeyboardButton("Сделка закрыта ✅", callback_data=f"status_closed={user_id}"))
    keyboard.add(InlineKeyboardButton("Отказ ❌️", callback_data=f"status_declined={user_id}"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data=f"i={user_id}"))
    return keyboard


def back_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data=f"i={user_id}"))
    return keyboard


def back_menu_btn():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data=f"back_menu"))
    return keyboard


async def add_comment_btn(user_id, element_id):
    from functions import is_agent
    keyboard = InlineKeyboardMarkup()

    if is_agent(user_id):
        keyboard.add(InlineKeyboardButton(
            f"💬 Добавить задачу", callback_data=f"set_comment={element_id}"
        ))

    return keyboard


def confirm_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_send"))
    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_send"))
    return keyboard


def reward_keyboard():
    keyboard = InlineKeyboardMarkup()
    reward_types = db.get_all_reward_types()
    for reward in reward_types:
        keyboard.add(InlineKeyboardButton(reward[0], callback_data=f"change_reward_{reward[0]}"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data=f"back_menu"))
    return keyboard

