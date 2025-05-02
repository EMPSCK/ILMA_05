import pymysql
import config
import asyncio
import os
import requests
from config import updatetime
from chairman_moves import generation_logic
from queries import chairman_queries_02
import json
from queries import general_queries

async def getJudName(id, compId):
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
            cur.execute(f"select firstName, lastName, skateId from competition_judges where id = {id}")
            ans = cur.fetchone()
            return ans
    except:
        return -1

async def pull_to_comp_group_jud(compId, crew_id, group):
    active_comp = compId
    linId = group['linId']
    zgsId = group['zgsId']
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
            for judIndex in range(len(zgsId)):
                i = zgsId[judIndex]
                ident = f'ЗГС'
                ans = await getJudName(i, compId)

                lastname = ans['lastName']
                firstname = ans['fistName']
                skateId =  ans['skateId']
                sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (crew_id, 1, ident, lastname, firstname, i, skateId))
                conn.commit()


            for judIndex in range(len(linId)):
                i = linId[judIndex]
                ans = await getJudName(i, compId)

                lastname = ans['lastName']
                firstname = ans['firstName']
                skateId = ans['skateId']

                ident = f'{ALPHABET[judIndex]}({judIndex + 1})'
                sql = "INSERT INTO competition_group_judges (`crewId`, `typeId`, `ident`, `lastName`, `firstName`, `judgeId`, `skateId`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (crew_id, 0, ident, lastname, firstname, i, skateId))
                conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1


async def pull_to_crew_group(active_comp, groupNumber, area):
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


async def get_group_name(compId, groupNumber):
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
            cur.execute(f"select groupName from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            r = cur.fetchone()
            return r['groupName']
    except:
        return -1

async def checkGenerationOrders():
    try:
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
                cur.execute(f"select * from generationRequests where isDone is null")
                results = cur.fetchall()
                for order in results:
                    compId = order['compId']
                    regionId = order['regionId']
                    groupList = list(map(int, order['groupNumbers'].split(';')))

                    data = {'compId': compId, "regionId": regionId, "status": 12, "groupList": groupList}
                    text, json_export = await generation_logic.get_ans(data)
                    json_final = {}
                    json_status = {}
                    have_mist = 0
                    for key in json_export:
                        json_status[key] = {}
                        json_final[key] = {}
                        json_status[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['linId'] = json_export[key].get('lin_id', [])
                        json_final[key]['zgsId'] = json_export[key].get('zgs_id', [])
                        if json_export[key]['status'] == 'fail':
                            have_mist = 1
                            msg = json_export[key]['msg']
                            if msg == '❌Не удалось сформировать бригаду с учетом заданных условий. Попробуйте уменьшить количество ЗГС':
                                json_final[key]['status'] = 2
                            elif msg == '❌Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерировать еще раз или уменьшить количество судей в бригаде.':
                                json_final[key]['status'] = 3
                            elif msg == '❌Группа не была обнаружена':
                                json_final[key]['status'] = 1
                            else:
                                json_final[key]['status'] = -1
                        else:
                            json_export[key]['status'] = 0
                        json_status[key]['status'] = json_export[key]['status']

                    json_final_01 = json_final.copy()
                    json_final = json.dumps(json_final, ensure_ascii=False)
                    json_status = json.dumps(json_status, ensure_ascii=False)
                    if have_mist == 0:
                        crewList = []
                        for i in groupList:
                            groupName = await get_group_name(compId, i)
                            crewId = await pull_to_crew_group(compId, i, groupName)
                            crewList.append(str(crewId))
                            key = 0
                            for j in json_final_01:
                                if json_final_01[j]['group_number'] == i:
                                    key = j
                                    break

                            group = json_final_01[key]

                            status = await pull_to_comp_group_jud(compId, crewId, group)


                    s = ';'.join(crewList)
                    cur.execute(f"update generationRequests set responseText = '{json_final}', statusId = {have_mist} where requestId = {order['requestId']}")
                    cur.execute(f"update generationRequests set status = '{json_status}', crewId = '{s}' where requestId = {order['requestId']}")
                    cur.execute(f"update generationRequests set isDone = 1 where requestId = {order['requestId']}")

                    conn.commit()
            await asyncio.sleep(15)
    except Exception as e:
        print(e)
