import pymysql
import config
from queries import general_queries
from queries import chairman_queries
from chairman_moves import check_list_judges
import re
import datetime
from datetime import date

async def pull_to_crew_group(user_id, groupNumber, area):
    active_comp = await general_queries.get_CompId(user_id)
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
            sql = "INSERT INTO competition_group_crew (`compId`, `groupNumber`, `roundName`) VALUES (%s, %s, %s)"
            cur.execute(sql, (
                active_comp, groupNumber, area))
            conn.commit()
            return cur.lastrowid
    except:
        return -1

async def name_to_jud_id(last_name, name, compId):
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
            cur.execute(f"select id, skateId from competition_judges where compId = {compId} and (lastName = '{last_name}' and firstName = '{name}')")
            ans = cur.fetchone()
            if ans is None:
                return {'id': -100, 'skateId': -100}
            else:
                if ans is None:
                    return {'id': -100, 'skateId': -100}
                else:
                    return ans
    except:
        return -1

async def pull_to_comp_group_jud(user_id, crew_id, area, have):
    gs, zgs, lin = have
    active_comp = await general_queries.get_CompId(user_id)
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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
            if gs != [[]]:
                for judIndex in range(len(gs)):
                    i = gs[judIndex].split()
                    if len(i) == 2:
                        lastname, firstname = i
                    else:
                        lastname = i[0]
                        firstname = ' '.join(i[1::])
                    ans = await name_to_jud_id(lastname, firstname, active_comp)
                    judge_id = ans['id']
                    skateId = ans['skateId']
                    ident = f'Гл. судья'
                    sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(sql, (crew_id, 2, ident, lastname, firstname, judge_id, skateId))
                    conn.commit()

            for judIndex in range(len(zgs)):
                i = zgs[judIndex].split()
                if len(i) == 2:
                    lastname, firstname = i
                else:
                    lastname = i[0]
                    firstname = ' '.join(i[1::])
                ans = await name_to_jud_id(lastname, firstname, active_comp)
                judge_id = ans['id']
                skateId = ans['skateId']
                ident = f'ЗГС'
                sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (crew_id, 1, ident, lastname, firstname, judge_id, skateId))
                conn.commit()


            for judIndex in range(len(lin)):
                i = lin[judIndex].split()
                if len(i) == 2:
                    lastname, firstname = i
                else:
                    lastname = i[0]
                    firstname = ' '.join(i[1::])
                ans = await name_to_jud_id(lastname, firstname, active_comp)
                judge_id = ans['id']
                skateId = ans['skateId']
                ident = f'{ALPHABET[judIndex]}({judIndex + 1})'
                sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (crew_id, 0, ident, lastname, firstname, judge_id, skateId))
                conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1

async def set_sex_for_judges(user_id):
    active_comp = await general_queries.get_CompId(user_id)
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
            cur.execute(f"select id, firstName, lastName, SecondName from competition_judges where compId = {active_comp} and gender is NULL")
            judges = cur.fetchall()


            for jud in judges:
                name = jud['firstName'].strip()
                sex = await get_gender(name)
                if sex is not None:
                    cur.execute(f"update competition_judges set gender = {sex} where id = {jud['id']}")
                    conn.commit()
                else:
                    sql = "INSERT INTO gender_unknown (`lastName`, `firstName`, `secondName`) VALUES (%s, %s, %s)"
                    cur.execute(sql,
                                (jud['lastName'], jud['firstName'], jud['SecondName']))
                    conn.commit()
    except Exception as e:
        print(e, 2)
        return -1


async def check_gender_zgs(user_id, zgs):
    if len(zgs) == 0:
        return 0, ''
    active_comp = await general_queries.get_CompId(user_id)
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
            genders = []
            for jud in zgs:
                i = jud.split()
                if len(i) == 2:
                    lastname, firstname = i
                else:
                    lastname = i[0]
                    firstname = ' '.join(i[1::])
                cur.execute(f"select gender from competition_judges where compId = {active_comp} and ((firstName = '{firstname}' and lastName = '{lastname}') or (firstName2 = '{firstname}' and lastName2 = '{lastname}'))")
                ans = cur.fetchone()
                if ans is not None:
                    if ans['gender'] is not None:
                        genders.append(ans['gender'])
            genders = set(genders)
            if 0 not in genders:
                return 1, 'гендерное распределение среди згс нарушает регламент'
            else:
                return 0, ''


    except Exception as e:
        print(e)
        return -1

async def judgeId_to_name(judge_id):
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
            cur.execute(f"select lastName, firstName, workCode, skateId from competition_judges where id = {judge_id}")
            ans = cur.fetchone()
            return ans


    except Exception as e:
        print(e)
        return -1


async def save_generate_result_to_new_tables(user_id, data):
    active_comp = await general_queries.get_CompId(user_id)
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
            for groupnumber in data:
                if data[groupnumber]['status'] != 'success':
                    continue

                groupNumber = data[groupnumber]['group_number']
                #Создаем запись в competition_group_crew
                cur.execute(f"select * from competition_group where compId = {active_comp} and groupNumber = {groupNumber}")
                ans = cur.fetchone()
                groupName = ans['groupName']
                sql = "INSERT INTO competition_group_crew (`compId`, `groupNumber`, `roundName`) VALUES (%s, %s, %s)"
                cur.execute(sql, (
                    active_comp, groupNumber, groupName))
                conn.commit()
                crew_id = cur.lastrowid
                #Докидываем судей в competition_group_judges
                ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                lin_id = data[groupnumber]['lin_id']
                zgs_id = data[groupnumber]['zgs_id']
                zgs_data = []
                lin_data = []

                for judIdIndex in range(len(zgs_id)):
                    info = await judgeId_to_name(zgs_id[judIdIndex])
                    lastname = info['lastName']
                    firstname = info['firstName']
                    skateId = info['skateId']
                    zgs_data.append({'judgeId': zgs_id[judIdIndex], 'lastname':lastname, 'firstname':firstname, 'skateId': skateId})

                zgs_data.sort(key=lambda x: x['lastname'])
                for jud in zgs_data:
                    ident = 'ЗГС'
                    lastname = jud['lastname']
                    firstname = jud['firstname']
                    skateId = jud['skateId']
                    judgeid = jud['judgeId']
                    sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(sql, (crew_id, 1, ident, lastname, firstname, judgeid, skateId))
                    conn.commit()

                for judIdIndex in range(len(lin_id)):
                    info = await judgeId_to_name(lin_id[judIdIndex])
                    lastname = info['lastName']
                    firstname = info['firstName']
                    skateId = info['skateId']
                    lin_data.append({'judgeId': lin_id[judIdIndex], 'lastname':lastname, 'firstname':firstname, 'skateId': skateId})

                lin_data.sort(key=lambda x: x['lastname'])
                for i in range(len(lin_data)):
                    ident = f'{ALPHABET[i]}({i + 1})'
                    lastname = lin_data[i]['lastname']
                    firstname = lin_data[i]['firstname']
                    skateId = lin_data[i]['skateId']
                    judgeid = lin_data[i]['judgeId']
                    sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(sql, (crew_id, 0, ident, lastname, firstname, judgeid, skateId))
                    conn.commit()

    except Exception as e:
        print(e)
        return -1


async def get_gender(firstName):
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
            cur.execute(f"select gender from gender_encoder where firstName = '{firstName}'")
            ans = cur.fetchone()
            if ans is None:
                return None
            else:
                return ans['gender']
    except Exception as e:
        print(e)
        return None

async def active_group(compId, groupNumber):
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
            cur.execute(f"select isActive from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            ans = cur.fetchone()
            if ans is None:
                return 0
            else:
                r = ans['isActive']
                if r is None:
                    return 0
                else:
                    return r

    except Exception as e:
        print(e)
        return 0


async def get_message_about_age(user_id, judges, code):
    msg = ''
    try:
        if not(code == 0 or code == 1):
            return -1

        compid = await general_queries.get_CompId(user_id)
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
            for jud in judges:
                last_name, name = jud
                cur.execute(f"select Birth from competition_judges where compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                date = cur.fetchone()

                cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {compid}")
                ans = cur.fetchone()
                date1, date2 = ans['date1'], ans['date2']
                if date is None:
                    continue
                else:
                    date = date['Birth']
                    if date is None or type(date) == str:
                        continue

                if code == 1 or code == 2 or code == 0:

                    age = date2.year - date.year
                    if not (28 <= age <= 75):
                        msg += f"🤔{last_name} {name} не попадает в возрастную категорию 28 - 75 лет.\n\n"
            if msg == '':
                return 0
            return msg

    except Exception as e:
        print(e)
        return 0



async def check_age_cat(user_id, lin, zgs, gs):
    try:
        compid = await general_queries.get_CompId(user_id)
        msg = ''
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
            if len(gs) == 0:
                judges = lin + zgs
            else:
                judges = lin + zgs + [gs]

            for jud in judges:
                i = jud.split()
                if len(i) == 2:
                    last_name, name = i
                else:
                    last_name = i[1]
                    name = ' '.join(i[1::])

                cur.execute(f"select Birth from competition_judges where compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                date = cur.fetchone()

                cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {compid}")
                ans = cur.fetchone()
                date1, date2 = ans['date1'], ans['date2']
                if date is None:
                    continue
                else:
                    date = date['Birth']
                    if date is None or type(date) == str:
                        continue

                age = date2.year - date.year

                if jud == gs:
                    if not (30 <= age <= 75):
                        msg += f"-{last_name} {name} не попадает в возрастную категорию 28 - 75 лет.\n\n"
                else:
                    if not (28 <= age <= 75):
                        msg += f"-{last_name} {name} не попадает в возрастную категорию 28 - 75 лет.\n\n"

            if msg != '':
                return 1, msg

            return 0, ''
    except:
        return 0, ''


async def age_filter(all_judges, compId):
    try:
        all_judges_01 = []
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {compId}")
            ans = cur.fetchone()
            date1, date2 = ans['date1'], ans['date2']
            if date2 is None:
                return all_judges

        for jud in all_judges:
            date = jud['Birth']
            if date is None or type(date) == str:
                all_judges_01.append(jud)
                continue

            age = date2.year - date.year
            if 28 <= age <= 75:
                all_judges_01.append(jud)


        return all_judges_01
    except Exception as e:
        print(e)
        return all_judges


async def sort_generate_list(json, user_id):
    try:
        compid = await general_queries.get_CompId(user_id)
        text = []
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
            for groupNumber in json:
                group_number = json[groupNumber]['group_number']
                cur.execute(f"select groupName from competition_group where compId = {compid} and groupNumber = {group_number}")
                groupName = cur.fetchone()
                if groupName is None:
                    groupName = 'Группа'
                else:
                    groupName = groupName['groupName']
                info = json[groupNumber]

                text_01 = ''
                text_02 = []
                text_03 = []
                for lin in info['lin_id']:
                    cur.execute(f"select firstName, lastName from competition_judges where id = {lin}")
                    names = cur.fetchone()
                    if names is None:
                        text_02.append("Фамилия Имя")
                    else:
                        text_02.append(f"{names['lastName']} {names['firstName']}")

                if info['zgs_id'] != []:
                    for zgs in info['zgs_id']:
                        cur.execute(f"select firstName, lastName from competition_judges where id = {zgs}")
                        names = cur.fetchone()
                        if names is None:
                            text_03.append("Фамилия Имя")
                        else:
                            text_03.append(f"{names['lastName']} {names['firstName']}")

                text_02.sort()
                text_03.sort()
                if len(text_03) != 0:
                    text_01 = str(group_number) + '. ' + groupName + '.' + '\n' + f'Згс. {", ".join(text_03)}'+ "\n" + f'Линейные судьи: {", ".join(text_02)}'
                else:
                    text_01 = str(group_number) + '. ' +  groupName + '.' + '\n' + f'Линейные судьи: {", ".join(text_02)}'
                text.append(text_01)

            r = "\n\n".join(text)
            return r


    except Exception as e:
        print(e)
        return -1


async def getSportCategoryEncoder():
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
            cur.execute(f"select * from judges_category_sport")
            ans = cur.fetchall()
            ans_01 = {}
            for cat in ans:
                ans_01[cat["categoryName"]] = cat["categoryId"]
            return ans_01
    except:
        return -1


async def checkSportCategoryFilter(lin, zgs, gs, user_id, group_num):
    try:
        msg = ''
        compid = await general_queries.get_CompId(user_id)
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
            cur.execute(f"select minCategorySportId, minCategoryZGSSportId  from competition_group where groupNumber = {group_num} and compId = {compid}")
            catfilter = cur.fetchone()
            if catfilter is None:
                return 0, ''


            catfilter_zgs = catfilter['minCategoryZGSSportId']
            catfilter = catfilter['minCategorySportId']


            if catfilter is None and catfilter_zgs is None:
                return 0, ''


            encoder = await getSportCategoryEncoder()
            if len(gs) == 0:
                judges = lin + zgs
            else:
                judges = lin + zgs + [gs]


            for jud in lin:
                i = jud.split()
                if len(i) == 2:
                    last_name, name = i
                else:
                    last_name = i[0]
                    name = ' '.join(i[1::])
                cur.execute(f"SELECT * from competition_judges WHERE compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                ans = cur.fetchone()
                if ans is None:
                    continue

                sportCat = ans['SPORT_Category_Id']
                if sportCat is None:
                    msg += f"{last_name} {name} - нет спортивной категории\n\n"
                    continue
                if sportCat < catfilter:
                    msg += f"{last_name} {name} - спортивная категория не соответствует минимально установленной для работы в группе\n\n"


            if zgs != [] and catfilter_zgs is not None:
                for jud in zgs:
                    i = jud.split()
                    if len(i) == 2:
                        last_name, name = i
                    else:
                        last_name = i[0]
                        name = ' '.join(i[1::])
                    cur.execute(
                        f"SELECT * from competition_judges WHERE compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                    ans = cur.fetchone()
                    if ans is None:
                        continue

                    sportCat = ans['SPORT_Category_Id']
                    if sportCat is None:
                        msg += f"{last_name} {name} - нет спортивной категории\n\n"
                        continue
                    elif sportCat < catfilter_zgs:
                        msg += f"{last_name} {name} - спортивная категория не соответствует минимально установленной для работы в группе\n\n"

            if msg == '':
                return 0, ''
            else:
                return 1, msg
    except Exception as e:
        print(e, 'checkSportCategoryFilter')
        return 0, ''
        pass

async def set_min_sport_cat(compId, group_num, cat):
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
            if cat == 5:
                cur.execute(
                    f"update competition_group set minCategorySportId = NULL where compId = {compId} and groupNumber = {group_num}")
                conn.commit()
                return 1
            cur.execute(f"update competition_group set minCategorySportId = {cat} where compId = {compId} and groupNumber = {group_num}")
            conn.commit()
            return 1
    except Exception as e:
        print(e)
        return 0

async def check_sport_cat_for_rep(all_judges, compId, groupNumber, judType):
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
            all_judges_01 = all_judges.copy()
            cur = conn.cursor()
            cur.execute(f"select minCategorySportId from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            mincat = cur.fetchone()
            if mincat is None:
                return all_judges
            mincat = mincat['minCategorySportId']

            if mincat is None:
                return all_judges

            cur.execute(f"select date2 from competition where compId = {compId}")
            date2 = cur.fetchone()
            date2 = date2['date2']
            for jud in all_judges:
                if jud['SPORT_Category_Id'] is None:
                    all_judges_01.remove(jud)

                elif jud['SPORT_Category_Id'] < mincat and judType == 'l':
                    all_judges_01.remove(jud)
                else:
                    CategoryDate = jud['SPORT_CategoryDate']
                    CategoryDateConfirm = jud['SPORT_CategoryDateConfirm']
                    catd = 0
                    if type(CategoryDate) == str and type(CategoryDateConfirm) == str:
                        all_judges_01.remove(jud)

                    elif type(CategoryDateConfirm) == str:
                        catd = CategoryDate
                    else:
                        catd = max(CategoryDate, CategoryDateConfirm)
                    a = date2 - catd
                    a = a.days
                    code = jud['SPORT_Category_Id']
                    if code == 2 or code == 3:
                        if a - 365 * 2 > 0:
                            all_judges_01.remove(jud)

                    elif code == 1:
                        if a - 365 > 0:
                            all_judges_01.remove(jud)

                    elif code == 4:
                        if a - 365 * 4 > 0:
                            all_judges_01.remove(jud)
        return all_judges_01


    except Exception as e:
        print(e)
        return all_judges


async def get_group_params(compId, groupNumber):
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
            cur.execute(f"select * from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            ans = cur.fetchone()
            if ans is None:
                return -1

            return ans
    except:
        return -1

async def agregate_check_func(gs, zgs, lin, groupNumber, user_id):
    try:
        msg = ''
        flag = 0
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        lin_vk_count = 0
        compId = await general_queries.get_CompId(user_id)
        group_params = await get_group_params(compId, groupNumber)
        if group_params == -1:
            return 0, ''

        with conn:
            cur = conn.cursor()
            if lin != []:
                for jud in lin:
                    i = jud.split()
                    if len(i) == 2:
                        last_name, name = i
                    else:
                        last_name = i[0]
                        name = ' '.join(i[1::])
                    cur.execute(
                        f"SELECT * from competition_judges WHERE compId = {compId} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                    ans = cur.fetchone()
                    if ans is None:
                        continue

                    if ans['SPORT_Category_Id'] == 4:
                        lin_vk_count += 1

            min_vk = group_params['minVK']
            if min_vk is None:
                min_vk = 0

            if lin_vk_count < min_vk:
                msg += f'Минимальное число линейных судей с всероссийской категорией - {min_vk}, в группе - {lin_vk_count}'
                flag = 1


            return flag, msg

    except Exception as e:
        print(e, 'agregate_check_func')
        return 0, ''

async def set_min_vk(compId, groupNumber, cat_id):
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
            cur.execute(f"update competition_group set minVK = {cat_id} where compId = {compId} and groupNumber = {groupNumber}")
            conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1
        pass



async def get_jud_info(judId):
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
            cur.execute(f"select * from competition_judges where id = {judId}")
            ans = cur.fetchone()
            if ans is None:
                return 'не найден'

            ftsarr_cat = ans['DSFARR_Category']
            if ftsarr_cat is None:
                ftsarr_cat = 'не определено'
            sport_cat = ans['SPORT_Category']
            if sport_cat is None:
                sport_cat = 'не определено'
            city = ans['City']
            if city is None:
                city = 'не определено'
            club = ans['Club']
            if club is None:
                club = 'не определено'
            firstName = ans['firstName']
            if firstName is None:
                firstName = 'не определено'
            lastName = ans['lastName']
            if lastName is None:
                lastName = 'не определено'

            workCode = ans['workCode']
            code_enc = {0: "Линейный судья", 2: "Гс", 1: "Згс", 3: "Спу", 4:'ГСС', 5:'ГСГСК'}


            return f'👨‍⚖️{lastName} {firstName}\nГород: {city}\nКлуб: {club}\nКатегория фтсарр: {ftsarr_cat}\nСпортивная категория: {sport_cat}\nРоль на площадке: {code_enc[workCode]}'
    except Exception as e:
        print(e)
        return '❌Ошибка'
        pass

async def change_sp(judgeId, code):
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
            cur.execute(f"update competition_judges set workCode = {code} where id = {judgeId}")
            conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1
        pass



def kill():
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
            cur.execute(f"select * from competition where isActive = 0")
            competitions = cur.fetchall()

            for comp in competitions:
                compId = comp['compId']

                cur.execute(f"delete from competition_files where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition_group where compId = {compId}")
                conn.commit()

                cur.execute(f'select id from competition_group_crew where compId = {compId}')
                crew_ids = cur.fetchall()
                crew_ids = [i['id'] for i in crew_ids]
                print(crew_ids)
                cur.execute(f"delete from competition_group_crew where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition_group_interdiction where compId = {compId}")
                conn.commit()

                cur.execute(f"select *  from competition_group_judges")
                ans = cur.fetchall()
                for jud in ans:
                    if jud['crewId'] in crew_ids:
                        cur.execute(f"delete from competition_group_judges where crewId = {jud['crewId']}")
                        conn.commit()

                cur.execute(f"delete from competition_judges where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition where compId = {compId}")
                conn.commit()


    except Exception as e:
        print(e)
        return -1

from chairman_moves import generation_logic
async def changeGenerationRandom(user_id):
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
            mode = await generation_logic.getRandomMode(active_comp)
            if mode == 0:
                cur.execute(f"update competition set generationRandomMode = 1 where compId = {active_comp}")
                conn.commit()
            elif mode == 1:
                a = cur.execute(f"update competition set generationRandomMode = 0 where compId = {active_comp}")
                conn.commit()
            return "✅Режим генерации изменен"
    except:
        return -1


async def getGenertionInfo(user_id):
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
            cur.execute(f"select * from competition where compId = {active_comp}")
            info = cur.fetchone()
            generation_mode = info['generation_mode']
            genertionRandomMode = info['generationRandomMode']
            modeEncoder = {1:'сохранение списков ГСС', 0:'отправка списков РСК'}
            text = f'🗓<b>Режим генерации: {modeEncoder[generation_mode]}</b>\n\n📋<b>Разброс по минимальным счетчикам судейств: {genertionRandomMode}</b>\nЧисло в диапазоне от 0 до 100.\n\n0 - равномерное распределение количества судейств между доступными судьями, меньшая степень ротации.\n\n100 - максимальная степень ротации, не учитывает равномерность количества судейств.'
            return text
    except Exception as e:
        print(e)
        return -1

async def setGenerationRandom(user_id, param):
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
            cur.execute(f'update competition set generationRandomMode = {param} where compId = {active_comp}')
            conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1

async def setGenMode(user_id):
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
            cur.execute(f'select generation_mode from competition where compId = {active_comp}')
            mode = cur.fetchone()
            mode = mode['generation_mode']
            if mode == 1:
                cur.execute(f'update competition set generation_mode = 0 where compId = {active_comp}')
                conn.commit()
            else:
                cur.execute(f'update competition set generation_mode = 1 where compId = {active_comp}')
                conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1
