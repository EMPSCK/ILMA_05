import re
import sqlite3
from itertools import combinations
from queries import general_queries
from queries import chairman_queries
from queries import chairman_queries_02
import config
import pymysql
from handlers import Chairman_comm_handler

async def check_list(text, user_id):
    try:
        groupNumbers = set()
        areas_01 = []
        s = ''
        list_for_group_counter = []
        flag1, flag2, flag3, flag4, flag5, flag6, flag7, flag8, flag9, flag10, flag11, flag12, flag13 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        flag14, flag15, flag17 = 0, 0, 0
        active_comp = await general_queries.get_CompId(user_id)
        const = await general_queries.get_tournament_lin_const(active_comp)
        judges_free = await general_queries.get_judges_free(active_comp)
        judges_free = [[i['lastName'], i['firstName'], i['bookNumber']] for i in judges_free]


        # Разбиваем текст сообщения на площадки по переносам строки, у строк с судьями по краям обрезаем переносы/пробелы/точки
        areas = re.split('\n\s{0,}\n', text)
        areas_02 = areas.copy()
        areas = [re.split('Гс.?\s{1,}|Згс.?\s{1,}|Линейные судьи\s{0,}.?\s{1,}', i) for i in areas]
        areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
        sumjudes = []
        new_text = ''
        # На каждой из площадок получаем линейных и остальных судей
        for areaindex in range(len(areas)):
            area = areas[areaindex]
            if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
                continue
                area[0] = area[0].split('\n')
                for i in range(len(area[0])):
                    area[0][i] = area[0][i].replace('ГСС. ', '')
                    area[0][i] = area[0][i].replace('ГСек.', '')
                    area[0][i] = area[0][i].strip().strip('.').strip('\n')
                otherjud = area[0]
                k = await chairman_queries.check_category_date(otherjud, user_id)
                if k != 0:
                    flag6 = 1
                    s += f'❌Ошибка: {area}: {k}\n\n'
                sumjudes.append(set(otherjud))
            else:
                '''
                linjud = re.split(',\s{0,}', area[-1])
                list_for_group_counter += linjud
                otherjud = re.split(',\s{0,}', ', '.join([area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))
                '''

                have_gs = 0
                have_lin = 0
                have_zgs = 0
                lin = []
                zgs = []
                gs = []
                #print(areas_02[areaindex])
                if re.search('Гс.?\s{1,}', areas_02[areaindex]): have_gs = 1
                if re.search('Згс.?\s{1,}', areas_02[areaindex]): have_zgs = 1
                if 'Линейные' in areas_02[areaindex]: have_lin = 1

                if have_lin == 1 and have_gs == 1 and have_zgs == 1:
                    gs = area[1]
                    zgs = re.split(',\s{0,}', area[2])
                    lin = re.split(',\s{0,}', area[3])
                    zgs.sort()
                    lin.sort()
                    new_text += f'{area[0]}\nГс. {gs}\nЗгс. {", ".join(zgs)}\nЛинейные судьи: {", ".join(lin)}\n\n'
                elif have_gs == 0 and have_zgs == 1 and have_lin == 1:
                    zgs = re.split(',\s{0,}', area[1])
                    lin = re.split(',\s{0,}', area[2])
                    zgs.sort()
                    lin.sort()
                    new_text += f'{area[0]}\nЗгс. {", ".join(zgs)}\nЛинейные судьи: {", ".join(lin)}\n\n'
                elif have_gs == 1 and have_zgs == 0 and have_lin == 1:
                    gs = area[1]
                    lin = re.split(',\s{0,}', area[2])
                    lin.sort()
                    new_text += f'{area[0]}\nГс. {gs}\nЛинейные судьи: {", ".join(lin)}\n\n'
                elif have_gs == 0 and have_zgs == 0 and have_lin == 1:#
                    lin = re.split(',\s{0,}', area[1])
                    lin.sort()
                    new_text += f'{area[0]}\nЛинейные судьи: {", ".join(lin)}\n\n'



                '''
                if len(gs.split(',')) >= 2:
                    s += f'❌Ошибка: {area[0]}: некорректный формат списка\n\n'
                    flag15 = 1
                    continue
                '''

                linjud = lin.copy()
                otherjud = [gs] + zgs
                if otherjud[0] == []:
                    otherjud.pop(0)
                list_for_group_counter += linjud

                area_01 = area.copy()
                area = area[0]
                if len(lin) != len(set(lin)):
                    flag17 = 1
                    s += f'❌Ошибка: {area}: дублирование внутри линейных судей\n\n'

                if len(zgs) != len(set(zgs)):
                    flag17 = 1
                    s += f'❌Ошибка: {area}: дублирование внутри згс\n\n'


                #group_num = re.search('Гр.\s{0,}\d+', area)
                group_num = re.search('\d+.', area[0:5].strip())
                areas_01.append([area, area_01, areas_02[areaindex], group_num, [[gs], zgs, lin]])
                if group_num is not None and not area[0].isalpha():
                    group_num = int(group_num[0].replace('.', '').strip())
                    groupNumbers.add(group_num)
                    status = await chairman_queries_02.active_group(active_comp, group_num)
                    if status == 0:
                        flag10 = 1
                        s += f'❌Ошибка: {area}: Группа не активна\n\n'
                        continue

                    groupType = await chairman_queries.is_rc_a(group_num, active_comp)


                    k7 = await chairman_queries.check_min_category(otherjud, linjud, group_num, active_comp, area)
                    if k7 != 1:
                        flag7 = 1
                        s += k7

                    k2 = await chairman_queries.group_id_to_lin_const(active_comp, group_num)
                    if k2 != 0 and k2 is not None:
                        const = k2

                    if groupType == 1:
                        k9, msg = await chairman_queries_02.check_gender_zgs(user_id, zgs)
                        if k9 == 1:
                            flag9 = 1
                            s += f'❌Ошибка: {area}: {msg}\n\n'

                        j1, msg = await chairman_queries_02.check_age_cat(user_id, lin, zgs, gs)
                        if j1 == 1:
                            flag11 = 1
                            s += f'❌Ошибка: {area}:\n{msg}'


                        j2, msg = await chairman_queries_02.checkSportCategoryFilter(lin, zgs, gs, user_id, group_num)
                        if j2 == 1:
                            flag12 = 1
                            s += f'❌Ошибка: {area}:\n{msg}'


                        k = await chairman_queries.check_category_date(otherjud + linjud, user_id)
                        if k != 0:
                            flag6 = 1
                            s += f'❌Ошибка: {area}: {k}\n\n'


                        k3, msg = await chairman_queries_02.agregate_check_func(gs, zgs, lin, group_num, user_id)
                        if k3 != 0:
                            flag13 = 1
                            s += f'❌Ошибка: {area}: {msg}\n\n'

                else:
                    flag14 = 1
                    s += f'❌Ошибка: {area}: не обнаружен номер группы\n\n'
                    continue


                if '' in otherjud:
                    otherjud = []


                k1 = await chairman_queries.check_clubs_match(linjud)
                if k1 != 0:
                    s += f'❌Ошибка: {area}: Распределение линейной группы по клубам нарушает регламент\n{k1}\n'
                    flag5 = 1


                # Проверяем количество линейных
                if len(linjud) != const:
                    s += f'❌Ошибка: {area}: количество членов линейной группы не соответствует установленной норме ({const}), на площадке - {len(linjud)}\n\n'
                    flag1 = 1


                if flag1 == 0 and group_num is not None:
                    groupType = await chairman_queries.is_rc_a(group_num, active_comp)
                    if groupType == 0:
                        msg, flag8 = await chairman_queries.check_rc_a_regions_VE(linjud, active_comp, group_num)
                        if flag8 == 1:
                            s += f"❌Ошибка: {area}: {msg}"


                # Проверяем совмещение должностей на площадке
                if len(set(otherjud) & set(linjud)) != 0:
                    flag4 = 1
                    a = ', '.join(map(str, set(otherjud) & set(linjud)))
                    s += f'🤔{area}: {a} совмеща(ет/ют) должности внутри площадки\n\n'

                sumjudes.append(set(otherjud + linjud))


        # Проверяем пересечения между площадками
        res = list(combinations(sumjudes, 2))
        res = [i[0] & i[1] for i in res if i[0] & i[1] != set()]
        if res != []:
            a = ', '.join(map(str, res[0]))
            s += f'❌Ошибка: {a}: работа(ет/ют) одновременно на нескольких площадках\n\n'
            flag3 = 1

        # Находим не задействованных на площадках судей
        # Находим тех, кто не бьется по judges_competition
        all_judges_areas = set()
        for i in sumjudes:
            all_judges_areas |= i

        judges_use = []
        for i in all_judges_areas:
            if len(i.split()) == 2:
                k = i.split()
                firstname = k[1]
                lastname = k[0]
            else:
                k = i.split()
                firstname = ' '.join(k[1::])
                lastname = k[0]
            for j in judges_free:
                if (j[1] == firstname and j[0] == lastname):
                    judges_use.append(j)
                    break


        config.judges_index[user_id] = judges_use
        Chairman_comm_handler.linsets[user_id][0] = new_text[0:-2]



        if flag1 + flag2 + flag3 + flag4 + flag5 + flag6 + flag7 + flag8 + flag9 + flag10 + flag12 + flag11 + flag13 + flag14 + flag15 + flag17== 0:
            for data in areas_01:
                # Новая логика для двух таблиц
                group_num = data[3]
                if group_num is not None:
                    group_num = int(group_num[0].replace('.', '').strip())
                    crew_id = await chairman_queries_02.pull_to_crew_group(user_id, group_num, data[0])
                    have = data[4]
                    if crew_id != -1:
                        await chairman_queries_02.pull_to_comp_group_jud(user_id, crew_id, data[1], have)
            return (1, s, list_for_group_counter)
        elif flag4 == 1 and flag1 + flag2 + flag3 + flag5 + flag6 + flag7 + flag8 + flag9 + flag10 + flag11 + flag12 + flag13 + flag14 + flag15 + flag17 == 0:
            for data in areas_01:
                # Новая логика для двух таблиц
                group_num = data[3]
                if group_num is not None:
                    group_num = int(group_num[0].replace('.', '').strip())
                    crew_id = await chairman_queries_02.pull_to_crew_group(user_id, group_num, data[0])
                    have = data[4]
                    if crew_id != -1:
                        await chairman_queries_02.pull_to_comp_group_jud(user_id, crew_id, data[1], have)
            return (10, s, list_for_group_counter)
        else:
            return (0, s, list_for_group_counter)

    except Exception as e:
        print('Ошибка проверки списка судей на валидность')
        print(2, e)
        return (2, '', -1)


async def get_parse(text, user_id):
    judges_use = []
    judges_problem = []
    judges_problem_db = []
    active_comp = await general_queries.get_CompId(user_id)
    conn = pymysql.connect(
        host=config.host,
        port=3306,
        user=config.user,
        password=config.password,
        database=config.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    text = text.replace('Линейный судьи', 'Линейные судьи')
    areas = re.split('\n\s{0,}\n', text)
    areas = [re.split('Гс.?\s{1,}|Згс.?\s{1,}|Линейные судьи\s{0,}.?\s{1,}', i) for i in areas]
    areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
    with conn:
        cur = conn.cursor()
        for areaindex in range(len(areas)):
            area = areas[areaindex]
            if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
                continue
                area[0] = area[0].split('\n')
                for i in range(len(area[0])):
                    area[0][i] = area[0][i].replace('ГСС. ', '')
                    area[0][i] = area[0][i].replace('ГСек.', '')
                    area[0][i] = area[0][i].strip().strip('.').strip('\n')
                otherjud = area[0]
                linjud = []
            else:
                linjud = re.split(',\s{0,}', area[-1])
                otherjud = re.split(',\s{0,}', ', '.join(
                    [area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))


            if '' in otherjud:
                otherjud = []

            for i in otherjud + linjud:
                if len(i.split()) == 2:
                    k = i.split()
                    firstname = k[1]
                    lastname = k[0]

                elif len(i.split()) == 1:
                    lastname = re.search('^[А-ЯA-Z][а-яa-z]*', i)[0]
                    firstname = i.replace(lastname, '')
                    text = text.replace(lastname + firstname, lastname + ' ' + firstname)

                elif len(i.split()) > 2:
                    peopls = []
                    k = i.split()
                    p = 0
                    for j in range(len(k)):
                        if p == 1:
                            p = 0
                            print(k[j])
                            if k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                                lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                                firstname = k[j].replace(lastname, '').strip()
                                text = text.replace(lastname + firstname, lastname + ' ' + firstname + ',')
                                peopls.append([lastname, firstname])
                            continue

                        if k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                            lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                            firstname = k[j].replace(lastname, '').strip()
                            text = text.replace(lastname + firstname, lastname + ' ' + firstname + ',')
                            peopls.append([lastname, firstname])
                        else:
                            if j == len(k) - 1:
                                pass
                            else:
                                lastname, firstname = k[j], k[j + 1]
                                text = re.sub(fr'\s+{lastname}\s+{firstname}', ' ' + lastname + ' ' + firstname + ',', text)
                                peopls.append([lastname, firstname])
                                p = 1

                        if text[-1] == ',':
                            text = text[0:-1] + '.'



                        text = text.replace(',,', ',')
                        text = text.replace(',.', '')
                        text = text.replace(', .', '')
                        text = '\n\n'.join([i.strip(',') for i in re.split('\n\s{0,}\n', text)])

                    for people in peopls:
                        lastname, firstname = people
                        st1 = cur.execute(f"SELECT firstName, lastName, id From competition_judges WHERE (lastName = '{lastname}' OR lastName2 = '{lastname}') AND CompId = {active_comp} AND active = 1")
                        st1 = cur.fetchall()
                        if len(st1) == 1:
                            #text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                            text = re.sub(rf'{lastname}\s+{firstname}', st1[0]['lastName'] + ' ' + st1[0]['firstName'],text)
                            judges_use.append([lastname, firstname, st1[0]['id']])
                            continue

                        if cur.execute(
                                f"SELECT bookNumber FROM competition_judges WHERE firstName = '{firstname}' AND lastName = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:

                            if cur.execute(
                                    f"SELECT bookNumber FROM competition_judges WHERE firstName2 = '{firstname}' AND lastName2 = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                                judges_problem.append([lastname, firstname])
                            else:
                                judges_problem_db.append([lastname, firstname])
                else:
                    k = i.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]



                cur.execute(
                    f"SELECT firstName, lastName, id From competition_judges WHERE lastName2 = '{lastname}' and firstName2 = '{firstname}' AND CompId = {active_comp} AND active = 1")

                st1 = cur.fetchall()
                if len(st1) == 1:
                    #Заменить регуляркой
                    #text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                    text = re.sub(rf'{lastname}\s+{firstname}', st1[0]['lastName'] + ' ' + st1[0]['firstName'], text)
                    judges_use.append([st1[0]['lastName'], st1[0]['firstName'], st1[0]['id']])
                    continue

                cur.execute( f"SELECT firstName, lastName, id From competition_judges WHERE lastName = '{lastname}' AND CompId = {active_comp} AND active = 1")
                st1 = cur.fetchall()
                if len(st1) == 1:
                    # Заменить регуляркой
                    #text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                    text = re.sub(rf'{lastname}\s+{firstname}', st1[0]['lastName'] + ' ' + st1[0]['firstName'],text)
                    judges_use.append([st1[0]['lastName'], st1[0]['firstName'], st1[0]['id']])
                    continue

                if cur.execute(f"SELECT bookNumber FROM competition_judges WHERE firstName = '{firstname}' AND lastName = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                    cur.execute(f"SELECT lastName from competition_judges WHERE lastName = '{lastname}' AND active = 1")
                    ans1 = cur.fetchall()
                    cur.execute(f"SELECT lastName from competition_judges WHERE lastName2 = '{lastname}' AND active = 1")
                    ans2 = cur.fetchall()

                    if cur.execute(f"SELECT bookNumber FROM competition_judges WHERE firstName2 = '{firstname}' AND lastName2 = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                        if [lastname, firstname] not in judges_problem:
                            judges_problem.append([lastname, firstname])
                    else:
                        if [lastname, firstname] not in judges_problem_db:
                            judges_problem_db.append([lastname, firstname])

    config.judges_index[user_id] = judges_use
    return judges_problem, judges_problem_db, text



async def transform_linlist(text, judges, user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        cur = conn.cursor()
        with conn:
            for jud in judges:
                if jud[-1] == 'NoneSpace':
                    lastname, firstname = jud[0:2]
                    text = text.replace(lastname + firstname, lastname + ' ' + firstname)
                else:
                    lastname, firstname = jud
                    cur.execute(f"SELECT firstName, lastName FROM competition_judges WHERE firstName2 = '{firstname}' and lastName2 = '{lastname}' and compId = {active_comp}")
                    name = cur.fetchone()
                    text = text.replace(lastname + ' ' + firstname, name['lastName'] + ' ' + name['firstName'])
            return text
    except Exception as e:
        print(1, e)
        return 0


async def get_all_judges(text):
    areas = re.split('\n\s{0,}\n', text)
    areas = [re.split('Гс.?\s{1,}|Згс.?\s{1,}|Линейные судьи\s{0,}.?\s{1,}', i) for i in areas]
    areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
    sumjudes = []

    # На каждой из площадок получаем линейных и остальных судей
    for areaindex in range(len(areas)):
        area = areas[areaindex]
        if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
            continue
            area[0] = area[0].split('\n')
            for i in range(len(area[0])):
                area[0][i] = area[0][i].replace('ГСС. ', '')
                area[0][i] = area[0][i].replace('ГСек.', '')
                area[0][i] = area[0][i].strip().strip('.').strip('\n')
            otherjud = area[0]
            sumjudes += otherjud
        else:
            linjud = re.split(',\s{0,}', area[-1])
            otherjud = re.split(',\s{0,}', ', '.join(
                [area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))
            if '' in otherjud:
                otherjud = []
            sumjudes += linjud
            sumjudes += otherjud
    return sumjudes


async def set_group_counter_for_lin_list(judges, user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            judges_set = list(set(judges))
            for jud in judges_set:
                i = jud.split()
                if len(i) == 2:
                    lastname = i[0]
                    firstname = i[1]
                else:
                    lastname = i[0]
                    firstname = i[1::]
                cur.execute(f"update competition_judges set group_counter = group_counter + 1 where compId = {active_comp} and ((firstName = '{firstname}' and lastName = '{lastname}') or (firstName2 = '{firstname}' and lastName2 = '{lastname}'))")
                conn.commit()
        return 1
    except:
        return 0



async def log(tg_id, text):
    try:
        active_comp = await general_queries.get_CompId(tg_id)
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
            cur.execute(f"insert into log_check (text, compId, tgId) values ('{text}', {active_comp}, {tg_id})")
            conn.commit()
            return 1
    except Exception as e:
        print(e)
        return 0

