import pymysql
import config
import asyncio
import os
import requests
from config import updatetime
from chairman_moves import generation_logic
from queries import chairman_queries_02

async def pull_to_crew_group_02(compId, groupNumber, area):
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
                config, groupNumber, area))
            conn.commit()
            return cur.lastrowid
    except:
        return -1


async def save_generate_result_to_new_tables(compId, data):
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
                    code = '000'
                    if data[groupnumber]['msg'] == 'группа не была обнаружена':
                        code = '001'
                    elif data[groupnumber][
                        'msg'] == 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерирвать еще раз или уменьшить количество судей в бригаде':
                        code = '003'
                    elif data[groupnumber][
                        'msg'] == 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте уменьшить количество ЗГС':
                        code = '002'
                    crew_id = await pull_to_crew_group_02(compId, groupnumber, code)
                    continue

                # Создаем запись в competition_group_crew
                cur.execute(
                    f"select * from competition_group where compId = {compId} and groupNumber = {groupnumber}")
                ans = cur.fetchone()
                groupName = ans['groupName']
                sql = "INSERT INTO competition_group_crew (`compId`, `groupNumber`, `roundName`) VALUES (%s, %s, %s)"
                cur.execute(sql, (
                    compId, groupnumber, groupName))
                conn.commit()
                crew_id = cur.lastrowid
                # Докидываем судей в competition_group_judges
                ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                lin_id = data[groupnumber]['lin_id']
                zgs_id = data[groupnumber]['zgs_id']
                zgs_data = []
                lin_data = []

                for judIdIndex in range(len(zgs_id)):
                    info = await chairman_queries_02.judgeId_to_name(zgs_id[judIdIndex])
                    lastname = info['lastName']
                    firstname = info['firstName']
                    skateId = info['skateId']
                    zgs_data.append({'judgeId': zgs_id[judIdIndex], 'lastname': lastname, 'firstname': firstname,
                                     'skateId': skateId})

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
                    info = await chairman_queries_02.judgeId_to_name(lin_id[judIdIndex])
                    lastname = info['lastName']
                    firstname = info['firstName']
                    skateId = info['skateId']
                    lin_data.append({'judgeId': lin_id[judIdIndex], 'lastname': lastname, 'firstname': firstname,
                                     'skateId': skateId})

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


async def checkGenerationOrders():
    while True:
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
            cur.execute(f"select * from generationRequests")
            results = cur.fetchall()

            for order in results:
                compId = order['compId']
                regionId = order['regionId']
                groupList = list(map(int, order['groupNumbers'].split(';')))

                data = {'compId': compId, "regionId": regionId, "status": 12, "groupList": groupList}
                text, json = await generation_logic.get_ans(data)
                await save_generate_result_to_new_tables(compId, json)

                cur.execute(f"delete from generationRequests where requestId = {order['requestId']}")
                conn.commit()
        await asyncio.sleep(15)