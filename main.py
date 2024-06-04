import logging
from aiogram import types
from aiogram import executor
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified,  ChatNotFound, UserDeactivated, BotBlocked
from datetime import datetime
from loader import dp, db, bot

import texts
from states import Registration, CommentState, MessageState, ChangeReward
from keyboards import (get_phone_keyboard, get_key, search_menu,
                       status_keyboard, back_keyboard, add_comment_btn,
                       confirm_keyboard, reward_keyboard, back_menu_btn)
from functions import open_menu, is_agent, is_admin, get_user_group, get_user_status

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'], state='*')
async def start(m: types.Message, state: FSMContext):
    await state.finish()
    user_id = m.from_user.id
    username = m.from_user.username or ''

    if not username:
        await m.answer("Вам нужно установить имя пользователя в настройках Telegram перед регистрацией.")
        return

    ref_code = None
    if len(m.text.split()) > 1:
        ref_code = m.text.split()[1]

    if not db.user_exists(user_id):
        await registration_user(m, ref_code)
    else:
        if is_agent(user_id):
            await m.answer("Приветствуем, Агент!", reply_markup=await get_key(user_id))
            await open_menu(m, user_id)
        elif is_admin(user_id):
            await m.answer("Приветствуем, Администратор!", reply_markup=await get_key(user_id))
            await open_menu(m, user_id)
        else:
            await m.answer("Главное меню, реферала!", reply_markup=await get_key(user_id))


async def registration_user(m: types.Message, ref_code):
    async with dp.current_state(user=m.from_user.id).proxy() as data:
        data['ref_code'] = ref_code
    await m.answer("Введите Имя и Фамилию:")
    await Registration.full_name.set()


@dp.message_handler(state=Registration.full_name, content_types=types.ContentTypes.TEXT)
async def process_full_name(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['full_name'] = m.text
    await m.answer("Введите ваш номер телефона или отправьте его с помощью кнопки ниже:",
                   reply_markup=get_phone_keyboard())
    await Registration.phone_number.set()


@dp.message_handler(state=Registration.phone_number, content_types=types.ContentTypes.TEXT)
async def process_phone_number_text(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = m.text

    await save_user_data(m, state)


@dp.message_handler(state=Registration.phone_number, content_types=types.ContentTypes.CONTACT)
async def process_phone_number_contact(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = m.contact.phone_number

    await save_user_data(m, state)


async def save_user_data(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = m.from_user.id
        username = m.from_user.username
        full_name = data['full_name']
        phone_number = data['phone_number']
        reg_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        ref_code = data.get('ref_code', None)

        ref = 0
        if ref_code is not None:
            try:
                ref = int(ref_code)
                if is_agent(ref):
                    await bot.send_message(ref,
                                           f'❗️ <b>У вас новый реферал!</b>\n\n'
                                           f'🆔 <b>TG:</b> <i>{m.from_user.full_name} | @{username} | <code>{user_id}</code>\n</i>'
                                           f'🙎‍♂️ <b>ФИО:</b> <i><tg-spoiler>{full_name}</tg-spoiler></i>\n'
                                           f'☎️ <b>Телефон:</b> <i><tg-spoiler>{phone_number}</tg-spoiler></i>',
                                           reply_markup=await add_comment_btn(ref, user_id))
                else:
                    ref = 0
            except ValueError:
                ref = 0

        db.add_user(user_id, username, full_name, m.from_user.first_name, phone_number, ref, reg_date)

    await m.answer("Вы успешно зарегистрированы!", reply_markup=await get_key(user_id))
    await state.finish()


@dp.message_handler(commands=['send_contacts'])
async def send_contacts(m: types.Message):
    await m.answer("Пожалуйста, отправьте контакты из вашей телефонной книги по одному.")


@dp.message_handler(content_types=types.ContentTypes.CONTACT)
async def handle_contact(m: types.Message):
    contact = m.contact
    name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
    phone_number = contact.phone_number

    db.add_contact(name, phone_number)

    await m.answer(f"Контакт {name} с номером {phone_number} успешно сохранен.")


@dp.inline_handler(lambda query: True)
async def inline_query(e: types.InlineQuery):
    user_id = e.from_user.id
    query_text = e.query
    results = []

    if query_text.startswith('name=') and is_agent(user_id):
        query_text = query_text.replace('name=', '')
        users = db.get_refs(user_id)
        index = 0
        for user in users:
            status = get_user_status(user[0])
            comment = db.get_comment(user[0])

            stats = (
                f'<b>🆔 Telegram ID:</b> <code>{db.get_id(user[0])}</code>\n'
                f'<b>🆔 TG name:</b> {db.get_tgname(user[0])}\n'
                f'<b>🆔 Username:</b> @{db.get_username(user[0])}\n'
                f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(user[0])}\n'
                f'<b>☎️ Номер телефона:</b> {db.get_phone(user[0])}\n'
                f'<b>🔹 Статус заявки:</b> {status}\n'
                f'<b>💬 Комментарий:</b> {comment}\n'
                f'<b>🗓 Дата регистрации:</b> {db.get_date(user[0])}'
            )

            try:
                user_name = db.get_name(user[0])
                if not is_agent(user[0]) and user_name and query_text.lower() in user_name.lower():
                    if index == 25:
                        break
                    index += 1
                    results.append(types.InlineQueryResultArticle(
                        id=str(index),
                        title=user_name,
                        description=db.get_phone(user[0]),
                        input_message_content=types.InputTextMessageContent(
                            message_text=stats,
                            disable_web_page_preview=True),
                        reply_markup=await search_menu(user_id, user[0])
                    ))
            except Exception as a:
                logging.error(f"Ошибка обработки пользователя {user[0]}: {a}")

    elif query_text.startswith('user=') and is_admin(user_id):
        query_text = query_text.replace('user=', '')
        users = db.get_all()
        index = 0

        for user in users:
            status = get_user_status(user[0])
            group = get_user_group(user[0])
            comment = db.get_comment(user[0])
            stats = (
                f'<b>🆔 Telegram ID:</b> <code>{db.get_id(user[0])}</code>\n'
                f'<b>🆔 TG name:</b> {db.get_tgname(user[0])}\n'
                f'<b>🆔 Username:</b> @{db.get_username(user[0])}\n'
                f'<b>🪪 Группа:</b> {group}\n'
                f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(user[0])}\n'
                f'<b>☎️ Номер телефона:</b> {db.get_phone(user[0])}\n'
                f'<b>🔹 Статус заявки:</b> {status}\n'
                f'<b>💬 Комментарий агента:</b> {comment}\n'
                f'<b>🗓 Дата регистрации:</b> {db.get_date(user[0])}'
            )

            try:
                user_name = db.get_name(user[0])
                if user_name and query_text.lower() in user_name.lower():
                    if index == 25:
                        break
                    index += 1
                    results.append(types.InlineQueryResultArticle(
                        id=str(index),
                        title=user_name,
                        description=db.get_phone(user[0]),
                        input_message_content=types.InputTextMessageContent(
                            message_text=stats,
                            disable_web_page_preview=True),
                        reply_markup=await search_menu(user_id, user[0])
                    ))
            except Exception as a:
                logging.error(f"Ошибка обработки пользователя {user[0]}: {a}")

    await e.answer(results, cache_time=1)


@dp.callback_query_handler(lambda call: call.data.startswith('set_group='))
async def set_group(c: types.CallbackQuery):
    user_id = c.from_user.id
    element_id = c.data.replace('set_group=', '')
    status = get_user_status(element_id)
    group = get_user_group(element_id)
    comment = db.get_comment(element_id)

    if is_admin(user_id):
        if group != 'Агент':
            db.set_group(element_id, 1)
            new_group = 'Агент'
            await c.answer('Агент успешно назначен ✅')
            await bot.send_message(element_id, '❗️ Вам были выданы права доступа <b>агента</b>!')
        else:
            db.set_group(element_id, 0)
            new_group = 'Реферал'
            await c.answer('Агент успешно разжалован ❌')
            await bot.send_message(element_id, '❗️ Вы были сняты с должности <b>агента</b>!')

        try:
            user_info = (
                f'<b>🆔 Telegram ID:</b> <code>{db.get_id(element_id)}</code>\n'
                f'<b>🆔 TG name:</b> {db.get_tgname(element_id)}\n'
                f'<b>🆔 Username:</b> @{db.get_username(element_id)}\n'
                f'<b>🪪 Группа:</b> {new_group}\n'
                f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(element_id)}\n'
                f'<b>☎️ Номер телефона:</b> {db.get_phone(element_id)}\n'
                f'<b>🔹 Статус заявки:</b> {status}\n'
                f'<b>💬 Комментарий агента:</b> {comment}\n'
                f'<b>🗓 Дата регистрации:</b> {db.get_date(element_id)}'
            )

            if c.inline_message_id:
                await bot.edit_message_text(
                    user_info,
                    inline_message_id=c.inline_message_id,
                    reply_markup=await search_menu(user_id, element_id),
                    disable_web_page_preview=True
                )
            else:
                await c.message.edit_text(
                    user_info,
                    reply_markup=await search_menu(user_id, element_id),
                    disable_web_page_preview=True
                )
        except MessageNotModified:
            await c.answer(text='❕ Обновлений профиля не было найдено')


@dp.callback_query_handler(lambda call: call.data.startswith('choose_status='))
async def set_status(c: types.CallbackQuery):
    user_id = c.from_user.id
    element_id = c.data.replace('choose_status=', '')
    comment = db.get_comment(element_id)
    if is_admin(user_id):
        try:
            user_info = (
                f'<b>🆔 Telegram ID:</b> <code>{db.get_id(element_id)}</code>\n'
                f'<b>🆔 TG name:</b> {db.get_tgname(element_id)}\n'
                f'<b>🆔 Username:</b> @{db.get_username(element_id)}\n'
                f'<b>🪪 Группа:</b> {get_user_group(element_id)}\n'
                f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(element_id)}\n'
                f'<b>☎️ Номер телефона:</b> {db.get_phone(element_id)}\n'
                f'<b>🔹 Статус заявки:</b> {get_user_status(element_id)}\n'
                f'<b>💬 Комментарий агента:</b> {comment}\n'
                f'<b>🗓 Дата регистрации:</b> {db.get_date(element_id)}'
            )

            if c.inline_message_id:
                await bot.edit_message_text(
                    user_info,
                    inline_message_id=c.inline_message_id,
                    reply_markup=status_keyboard(element_id),
                    disable_web_page_preview=True
                )
            else:
                await c.message.edit_text(
                    user_info,
                    reply_markup=status_keyboard(element_id),
                    disable_web_page_preview=True
                )
        except MessageNotModified:
            await c.answer(text='❕ Обновлений профиля не было найдено')


@dp.callback_query_handler(lambda call: call.data.startswith(('status_waiting=', 'status_closed=', 'status_declined=')))
async def handle_status_change(c: types.CallbackQuery):
    user_id = c.from_user.id
    data = c.data.split('=')
    new_status = data[0]
    element_id = data[1]
    comment = db.get_comment(element_id)

    status_map = {
        'status_waiting': 0,
        'status_declined': 1,
        'status_closed': 2,
    }

    if new_status in status_map and is_admin(user_id):
        current_status = db.get_status(element_id)
        new_status_code = status_map[new_status]

        if current_status != new_status_code:
            db.set_status(element_id, new_status_code)

            user_info = (
                f'<b>🆔 Telegram ID:</b> <code>{db.get_id(element_id)}</code>\n'
                f'<b>🆔 TG name:</b> {db.get_tgname(element_id)}\n'
                f'<b>🆔 Username:</b> @{db.get_username(element_id)}\n'
                f'<b>🪪 Группа:</b> {get_user_group(element_id)}\n'
                f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(element_id)}\n'
                f'<b>☎️ Номер телефона:</b> {db.get_phone(element_id)}\n'
                f'<b>🔹 Статус заявки:</b> {get_user_status(element_id)}\n'
                f'<b>💬 Комментарий агента:</b> {comment}\n'
                f'<b>🗓 Дата регистрации:</b> {db.get_date(element_id)}'
            )

            if new_status == 'status_closed':
                agent_id = db.get_ref(element_id)
                agent_username = db.get_username(agent_id)
                await bot.send_message(agent_id, f"Закрылась сделка @{agent_username} - вознаграждение за сделку начислится в ближайшее время!")

            if c.inline_message_id:
                await bot.edit_message_text(
                    user_info,
                    inline_message_id=c.inline_message_id,
                    reply_markup=await search_menu(user_id, element_id),
                    disable_web_page_preview=True
                )
            else:
                await c.message.edit_text(
                    user_info,
                    reply_markup=await search_menu(user_id, element_id),
                    disable_web_page_preview=True
                )
    else:
        await c.answer(text='✅')



@dp.callback_query_handler(lambda c: c.data.startswith('i='), state='*')
async def update_user_info(c: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user_id = c.from_user.id
    element_id = c.data.replace('i=', '')

    if db.user_exists(element_id) is None:
        return

    status = get_user_status(element_id)
    group = get_user_group(element_id)
    comment = db.get_comment(element_id)
    user_info = (
            f'<b>🆔 Telegram ID:</b> <code>{db.get_id(element_id)}</code>\n'
            f'<b>🆔 TG name:</b> {db.get_tgname(element_id)}\n'
            f'<b>🆔 Username:</b> @{db.get_username(element_id)}\n'
            + (f'<b>🪪 Группа:</b> {group}\n' if is_admin(user_id) else '') +
            f'<b>👨‍💻 Имя Фамилия:</b> {db.get_name(element_id)}\n'
            f'<b>☎️ Номер телефона:</b> {db.get_phone(element_id)}\n'
            f'<b>🔹 Статус заявки:</b> {status}\n'
            + (f'<b>💬 Комментарий агента:</b> {comment}\n' if is_admin(user_id) else f'<b>💬 Комментарий:</b> {comment}\n') +
            f'<b>🗓 Дата регистрации:</b> {db.get_date(element_id)}\n'
    )

    try:
        if c.inline_message_id is not None:
            await bot.edit_message_text(
                user_info,
                disable_web_page_preview=True,
                reply_markup=await search_menu(user_id, element_id),
                inline_message_id=c.inline_message_id
            )
        else:
            await c.message.edit_text(
                user_info,
                disable_web_page_preview=True,
                reply_markup=await search_menu(user_id, element_id),
            )

    except MessageNotModified:
        await c.answer(text='❕ Обновлений профиля не было найдено')


@dp.callback_query_handler(lambda call: call.data.startswith('set_comment='))
async def set_comment(c: types.CallbackQuery):
    user_id = c.from_user.id
    element_id = c.data.replace('set_comment=', '')

    if is_agent(user_id) and db.get_ref(element_id) == user_id:
        text = (f'📝 <b>Напишите задачу для реферала '
                f'<a href="t.me/{db.get_username(element_id)}">{db.get_name(element_id)}</a></b>')

        await CommentState.text.set()
        state = dp.current_state(user=c.from_user.id)
        await state.update_data(element_id=element_id)

        if c.inline_message_id:
            await bot.edit_message_text(
                text,
                inline_message_id=c.inline_message_id,
                reply_markup=back_keyboard(element_id),
                disable_web_page_preview=True
            )
        else:
            await c.message.edit_text(
                text,
                reply_markup=back_keyboard(element_id),
                disable_web_page_preview=True
            )


@dp.message_handler(state=CommentState.text)
async def receive_comment(m: types.Message, state: FSMContext):
    user_data = await state.get_data()
    element_id = user_data.get('element_id')
    new_comment = m.text

    db.set_comment(element_id, new_comment)

    await m.answer(f'<b>✅ Задача для реферала <a href="t.me/{db.get_username(element_id)}">{db.get_name(element_id)}</a> установлена.</b>\n\n'
                   f'<b>💬 Новая задача:</b> <i>{new_comment}</i>',
                   disable_web_page_preview=True)
    await state.finish()


@dp.callback_query_handler(lambda call: call.data.startswith('send_message='))
async def start_send_message(c: types.CallbackQuery, state: FSMContext):
    user_id = c.from_user.id
    element_id = c.data.replace('send_message=', '')

    await MessageState.text.set()
    await state.update_data(element_id=element_id)

    text = f'📝 <b>Введите сообщение для <a href="t.me/{db.get_username(element_id)}">{db.get_name(element_id)}</a>:</b>'

    if c.message:
        await c.message.answer(text, reply_markup=back_keyboard(element_id),
                               disable_web_page_preview=True)
    elif c.inline_message_id:
        await bot.send_message(c.from_user.id, text, reply_markup=back_keyboard(element_id),
                               disable_web_page_preview=True)

    await c.answer()


@dp.message_handler(state=MessageState.text)
async def receive_message(m: types.Message, state: FSMContext):
    await state.update_data(message_text=m.text)

    await m.answer(f"⏳ <b>Подтвердите отправку:</b>\n\n{m.text}", reply_markup=confirm_keyboard(),
                   disable_web_page_preview=True)
    await MessageState.confirming_text.set()


@dp.callback_query_handler(lambda call: call.data == 'confirm_send', state=MessageState.confirming_text)
async def confirm_send_message(c: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    element_id = user_data['element_id']
    message_text = user_data['message_text']

    try:
        await bot.send_message(chat_id=element_id, text=message_text)
        await c.message.edit_text(f'📩 <b><a href="t.me/{db.get_username(element_id)}">{db.get_name(element_id)}</a> '
                                  f'успешно получил сообщение!</b>',
                                  disable_web_page_preview=True)
    except ChatNotFound:
        await c.message.edit_text("<b>❗️ Ошибка: Чат не найден. Пользователь может быть неактивен или заблокировал бота.</b>")
    except UserDeactivated:
        await c.message.edit_text("<b>❗️ Ошибка: Пользователь деактивировал свой аккаунт.</b>")
    except BotBlocked:
        await c.message.edit_text("<b>❗️ Ошибка: Бот заблокирован пользователем.</b>")
    except Exception as e:
        logging.exception(e)
        await c.message.edit_text("<b>❗️ Произошла ошибка при отправке сообщения.</b>")

    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'cancel_send', state=MessageState.confirming_text)
async def cancel_send_message(c: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    element_id = user_data['element_id']
    await c.message.edit_text("<b>❌ Отправка сообщения отменена.\n"
                              "Для возврата к меню нажмите кнопку ◀️ Назад</b>", reply_markup=back_keyboard(element_id))
    await state.finish()


@dp.message_handler(commands=['add_admin'])
async def add_admin(m: types.Message):
    user_id = m.from_user.id

    if is_admin(user_id):
        try:
            command_parts = m.text.split()
            if len(command_parts) != 2:
                await m.reply("Пожалуйста, укажите user_id. Пример: /add_admin 123456789")
                return

            new_admin_id = int(command_parts[1])
            if db.user_exists(new_admin_id):
                db.set_group(new_admin_id, 2)
                await m.reply(f"Пользователь с user_id {new_admin_id} был успешно добавлен в группу администраторов.")
            else:
                await m.reply("Пользователь с указанным user_id не существует.")
        except ValueError:
            await m.reply("Пожалуйста, укажите корректный user_id.")
        except Exception as e:
            logging.exception(e)
            await m.reply("Произошла ошибка при добавлении пользователя в группу администраторов.")
    else:
        await m.reply("У вас нет прав для выполнения этой команды.")


@dp.message_handler(commands=['award'])
async def award_user(m: types.Message):
    user_id = m.from_user.id

    if is_admin(user_id):
        try:
            command_parts = m.text.split(maxsplit=2)
            if len(command_parts) != 3:
                await m.reply("Укажите номер телефона и тип вознаграждения.\n"
                              "Пример: /award 1234567890 Отказное письмо\n\n"
                              "<b>Типы вознаграждения:</b>\n"
                              "<code>Отказное письмо</code>\n<code>Декларация 1Д</code>\n<code>Декларация 3Д</code>\n<code>Сертификат соответсвия</code>\n<code>СГР</code>")
                return

            phone_number = command_parts[1]
            award_type = command_parts[2]

            award_amount = db.get_reward_amount(award_type)
            if award_amount is None:
                await m.reply("Неверный тип вознаграждения. Проверьте правильность ввода.")
                return

            if db.user_exists_by_phone(phone_number):
                user_id = db.get_user_id_by_phone(phone_number)
                if is_agent(user_id):
                    db.add_to_balance(user_id, award_amount)
                    db.record_award(user_id, phone_number, award_type, award_amount)
                    await bot.send_message(user_id, f"💸 Вы получили вознаграждение в размере <b>{award_amount} ₽</b> за <b>{award_type}</b>!")
                    await m.reply(f"Пользователь с номером телефона <b>{phone_number}</b>\n"
                                  f"получил вознаграждение: <b>{award_type}</b> на сумму <b>{award_amount} ₽</b>.")
                else:
                    await m.reply("Пользователь с указанным номером телефона не является агентом.")
            else:
                await m.reply("Пользователь с указанным номером телефона не существует.")
        except ValueError:
            await m.reply("Пожалуйста, укажите корректный номер телефона и тип вознаграждения.")
        except Exception as e:
            logging.exception(e)
            await m.reply("Произошла ошибка при добавлении вознаграждения пользователю.")
    else:
        await m.reply("У вас нет прав для выполнения этой команды.")


@dp.callback_query_handler(lambda c: c.data == 'select_reward')
async def select_reward_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if not is_admin(user_id):
        await callback_query.message.reply("У вас нет прав для выполнения этой команды.")
        return

    reward_types = db.get_all_reward_types()
    reward_info = "\n".join([f"<i>{reward[0]} - <code>{db.get_reward_amount(reward[0])} ₽</code></i>" for reward in reward_types])

    await callback_query.message.edit_text(f"<b>Параметры вознаграждения:</b>\n\n"
                                           f"{reward_info}",
                                           reply_markup=reward_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('change_reward_'))
async def process_reward_callback(callback_query: types.CallbackQuery, state: FSMContext):
    reward_type = callback_query.data[len('change_reward_'):]
    amount = db.get_reward_amount(reward_type)
    await callback_query.message.edit_text(f"Сейчас установлено - <b><code>{amount}</code> рублей</b>\n\n"
                                           f"✍️ Введите новую сумму для <b>{reward_type}</b>:")
    async with state.proxy() as data:
        data['reward_type'] = reward_type
    await ChangeReward.amount.set()


@dp.message_handler(state=ChangeReward.amount, content_types=types.ContentTypes.TEXT)
async def process_new_amount(m: types.Message, state: FSMContext):
    async with state.proxy() as data:
        reward_type = data['reward_type']
        try:
            new_amount = int(m.text)
        except ValueError:
            await m.reply("Пожалуйста, введите корректную сумму.")
            return

        if db.update_reward_amount(reward_type, new_amount):
            await m.reply(f"Сумма вознаграждения для <b>{reward_type}</b> успешно установлена на <code><b>{new_amount} ₽</b></code>.")
        else:
            await m.reply("Произошла ошибка при обновлении суммы вознаграждения. Убедитесь, что тип вознаграждения введен правильно.")

    await state.finish()


@dp.message_handler(commands=['delete_user'])
async def delete_user(m: types.Message):
    user_id = m.from_user.id
    if is_admin(user_id):
        try:
            delete_id = int(m.text.split()[1])
        except Exception as e:
            await m.answer('<code>/delete_user user_id</code>')
            await m.answer(f'{e}')
            return
        try:
            db.delete_user(delete_id)
            await m.answer(f'{delete_id} - Удален из БД')
        except Exception as e:
            await m.answer(f"{e}")


@dp.message_handler(content_types='text', state='*')
async def get_text(m: types.Message, state: FSMContext):
    await state.finish()
    if m.text == 'Меню агента 🖥':
        await open_menu(m, m.from_user.id)
    elif m.text == 'Меню администратора 👨‍💻':
        await open_menu(m, m.from_user.id)
    elif m.text == 'Настройки ⚙️':
        await m.answer(texts.settings_text)
    elif m.text == 'Информация ℹ️':
        await m.answer(texts.info_text)
    elif m.text == 'Техническая поддержка 👨‍💻':
        await m.answer(texts.tech_text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
