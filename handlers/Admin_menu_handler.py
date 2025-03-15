from aiogram import Router, F
from aiogram import types

import config
from keyboards import admins_kb
from queries import get_user_status_query
from queries import admins_queries
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from admin_moves import update_fttsar_judges
from queries import scrutineer_queries
from aiogram.filters import Command
router = Router()
tg_id_to_CompId = {}

class Create_comp(StatesGroup):
    next_create_comp_state = State()

@router.message(Command("admin"))
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id in config.admins:
        await message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)
    else:
        await message.answer('❌Отказано в доступе')

@router.callback_query(F.data == 'back_bbb')
async def cmd_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id in config.admins:
        await call.message.edit_text('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)
    else:
        await call.message.edit_text('❌Отказано в доступе')

#Создать новый турнир
@router.callback_query(F.data == 'create_competition')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 1:
        text = 'В следующем сообщении отправьте значения столбцов:\n\ndate1: \ndate2: \ncompName: \ncity: \nchairman_Id:\nscrutineerId: \nlin_const: \nisActive: \nisSecret: '
        await call.message.answer(text=text, reply_markup=admins_kb.create_comp_kb)
        await state.set_state(Create_comp.next_create_comp_state)


@router.message(Create_comp.next_create_comp_state)
async def f2(message: Message, state: FSMContext):
    new_comp_status = await admins_queries.create_new_comp(message.text)
    if new_comp_status == 1:
        await message.answer('Запись создана')
        await message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)
        await state.clear()
    else:
        await message.answer('🤔Ошибка, попробуйте еще раз', reply_markup=admins_kb.create_comp_kb)



@router.callback_query(F.data == 'cancel_create_comp')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)


#Вывести список турниров
@router.callback_query(F.data == 'show_tournament_list')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 1:
        text = await admins_queries.get_tournament_list()
        await call.message.edit_text(text)
        await call.message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)


#Редактировать турнир
class Edit_comp(StatesGroup):
    next_edit_comp_state = State()
    next_edit_comp_state_2 = State()


@router.callback_query(F.data == 'edit_competition')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 1 or call.from_user.id in config.admins:
        text = 'Отправьте ид соревнования:'
        await call.message.edit_text(text=text, reply_markup=admins_kb.create_comp_kb)
        await state.set_state(Edit_comp.next_edit_comp_state)


@router.message(Edit_comp.next_edit_comp_state)
async def f2(message: Message, state: FSMContext):
    id = message.text
    comp_data = await admins_queries.get_tournament(id)
    if comp_data is None or comp_data == 0:
        await message.answer('Запись не найдена', reply_markup=admins_kb.create_comp_kb)
    else:
        tg_id_to_CompId[message.from_user.id] = id
        text = 'В следующем сообщении отправьте новые значения столбцов:\ndate1: \ndate2: \ncompName: \ncity: \nchairman_Id: \nscrutineerId: \nlin_const: \nisActive: \nisSecret: '
        await message.answer(str(comp_data)+'\n\n' + text, reply_markup=admins_kb.create_comp_kb)
        await state.set_state(Edit_comp.next_edit_comp_state_2)


@router.message(Edit_comp.next_edit_comp_state_2)
async def f2(message: Message, state: FSMContext):
    text = message.text
    edit_comp_status = await admins_queries.edit_tournament(tg_id_to_CompId[message.from_user.id], message.text)
    if edit_comp_status == 1:
        await message.answer('Запись обновлена')
        await message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)
        await state.clear()
    else:
        await message.answer('🤔Ошибка, попробуйте еще раз', reply_markup=admins_kb.create_comp_kb)


@router.message(Edit_comp.next_edit_comp_state_2)
async def f2(message: Message, state: FSMContext):
    text = message.text
    edit_comp_status = await admins_queries.edit_tournament(tg_id_to_CompId[message.from_user.id], message.text)
    if edit_comp_status == 1:
        await message.answer('Запись обновлена')
        await message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)
        await state.clear()
    else:
        await message.answer('🤔Ошибка, попробуйте еще раз', reply_markup=admins_kb.create_comp_kb)


@router.callback_query(F.data == 'update_fttsar_judges')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 1 or call.from_user.id in config.admins:
        await call.message.answer('Запущен процесс обновления данных\nПримерное время ожидания: 5 мин.')
        status = await update_fttsar_judges.update_judges_list()
        if status == 1:
            await call.message.answer('Процесс обновления данных завершен')
        else:
            await call.message.answer('❌Ошибка')


from aiogram.filters import Command

oldinfo = {}
@router.callback_query(F.data == 'edit_tournament')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 1 or call.from_user.id in config.admins:

        markup = await admins_kb.get_tour_list_markup()
        await call.message.edit_text('Выберите соревнование', reply_markup=markup)


@router.callback_query(F.data.startswith('tournament_edit_choice_'))
async def cmd_start(call: types.CallbackQuery):
    compId = int(call.data.replace('tournament_edit_choice_', ''))
    oldinfo[call.from_user.id] = {'compId': compId}
    text = await admins_queries.get_tour_info(compId)
    await call.message.edit_text(text, reply_markup=admins_kb.edit_tour_kb)



@router.callback_query(F.data == 'active_tour')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    try:
        user_status = await get_user_status_query.get_user_status(call.from_user.id)
        if user_status == 1 or call.from_user.id in config.admins:
            compId = oldinfo[call.from_user.id]['compId']
            await admins_queries.activate_tour(compId)
            text = await admins_queries.get_tour_info(compId)
            await call.message.edit_text(text, reply_markup=admins_kb.edit_tour_kb)
    except:
        await call.answer('✅Соревнование уже активно')


from handlers import start_stage_handler
@router.callback_query(F.data == 'delactive_tour')
async def cmd_start(call: types.CallbackQuery, state:FSMContext):
    try:
        user_status = await get_user_status_query.get_user_status(call.from_user.id)
        if user_status == 1 or call.from_user.id in config.admins:
            compId = oldinfo[call.from_user.id]['compId']
            await admins_queries.deactivatetour(compId)
            text = await admins_queries.get_tour_info(compId)
            await call.message.edit_text(text, reply_markup=admins_kb.edit_tour_kb)
    except:
        await call.answer('❌Соревнование уже неактивно')
