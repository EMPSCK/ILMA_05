from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date

cancel_button = [InlineKeyboardButton(text="Отменить операцию", callback_data='cancel_load')]
load_judges_kb = InlineKeyboardMarkup(inline_keyboard=[cancel_button])

menu_button_1 = [InlineKeyboardButton(text='Создать турнир', callback_data='create_competition')]
menu_button_2 = [InlineKeyboardButton(text='Редактировать турнир', callback_data='edit_competition')]
menu_button_3 = [InlineKeyboardButton(text='Вывести список турниров', callback_data='show_tournament_list')]
menu_button_4 = [InlineKeyboardButton(text='Обновить базу судей ФТСАРР', callback_data='update_fttsar_judges')]
menu_button_5 = [InlineKeyboardButton(text='Редактировать турнир', callback_data='edit_tournament')]
menu_kb = InlineKeyboardMarkup(inline_keyboard=[menu_button_5])


create_comp_button_2 = [InlineKeyboardButton(text='Вернуться к меню', callback_data='cancel_create_comp')]
create_comp_kb = InlineKeyboardMarkup(inline_keyboard=[create_comp_button_2])
import pymysql
import config
async def get_tour_list_markup():
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            now = date.today()
            cur.execute(f"select * from competition")
            ans = cur.fetchall()
            but = []
            but2 = []
            for competitionIndex in range(len(ans)):
                date2 = ans[competitionIndex]['date2']
                a = now - date2
                if a.days > 0:
                    continue

                compName = ans[competitionIndex]['compName']
                compId = ans[competitionIndex]['compId']
                but2.append(InlineKeyboardButton(text=compName, callback_data=f"tournament_edit_choice_{compId}"))
                if len(but2) == 2:
                    but.append(but2)
                    but2 = []
            if len(but2) == 0:
                b = [InlineKeyboardButton(text='Назад', callback_data=f"back_bbb")]
                but.append(b)
            else:
                but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_bbb"))
                but.append(but2)
            return InlineKeyboardMarkup(inline_keyboard=but)

    except Exception as e:
        print(e)
        return 0


edit_button_1 = InlineKeyboardButton(text='Активировать', callback_data='active_tour')
edit_button_2 = InlineKeyboardButton(text='Деактивировать', callback_data='delactive_tour')
edit_button_3 = InlineKeyboardButton(text='Назад', callback_data='edit_tournament')
edit_tour_kb = InlineKeyboardMarkup(inline_keyboard=[[edit_button_1, edit_button_2], [edit_button_3]])