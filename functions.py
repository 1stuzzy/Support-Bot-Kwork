from loader import db, bot
from keyboards import main_menu


async def open_menu(message, user_id: int):
    bot_me = await bot.get_me()
    phone = db.get_phone(user_id)
    refs = db.get_refs(user_id)
    if is_agent(user_id):
        await message.answer(f'<b>📝 Меню агента</b>\n\n'
                             f'<b>📱 Номер телефона:</b> <tg-spoiler>{phone}</tg-spoiler>\n'
                             f'<b>💰 Заработано:</b> {db.get_balance(user_id)} RUB\n'
                             f'<b>🤝 Мои рефералы:</b> {len(refs)}\n\n'
                             f'<b>🔗 Реферальная ссылка:</b>\n'
                             f' https://t.me/{bot_me.username}?start={user_id}',
                             reply_markup=main_menu(user_id))
    elif is_admin(user_id):
        ref = db.get_all_refs()
        agents = db.get_all_agents()

        await message.answer(f'<b>👨‍💻 Меню администратора</b>\n\n'
                             f'<b>💰 Всего заработано:</b> {db.get_total_balance()} RUB\n'
                             f'<b>🪪  Всего агентов:</b> {len(ref)}\n'
                             f'<b>🤝 Всего рефералов:</b> {len(agents)}',
                             reply_markup=main_menu(user_id))
    else:
        return


def is_admin(user_id: int):
    group = db.get_group(user_id)
    if group is not None and group == 2:
        return True
    return False


def is_agent(user_id: int):
    group = db.get_group(user_id)
    if group is not None and group == 1:
        return True
    return False


def get_user_group(user_id: int):
    group_code = db.get_group(user_id)
    if group_code == 1:
        return 'Агент'
    elif group_code == 2:
        return 'Администратор'
    return 'Реферал'


def get_user_status(user_id: int):
    status_code = db.get_status(user_id)
    if status_code == 1:
        return 'Отказ'
    elif status_code == 2:
        return 'Сделка закрыта'
    elif status_code == 0:
        return 'В обработке'
    elif is_agent(user_id) or is_admin(user_id):
        return '-'
    return 'Неизвестный статус'

