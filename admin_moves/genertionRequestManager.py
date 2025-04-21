import pymysql
import config
import asyncio
import os
import requests
from config import updatetime
from chairman_moves import generation_logic
from queries import chairman_queries_02
import json


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
                    for key in json_export:
                        json_status[key] = {}
                        json_final[key] = {}
                        json_status[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['group_number'] = json_export[key]['group_number']
                        json_final[key]['linId'] = json_export[key].get('lin_id', [])
                        json_final[key]['zgsId'] = json_export[key].get('zgs_id', [])
                        if json_export[key]['status'] == 'fail':
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


                    json_final = json.dumps(json_final, ensure_ascii=False)
                    json_status = json.dumps(json_status, ensure_ascii=False)

                    cur.execute(f"update generationRequests set responseText = '{json_final}' where requestId = {order['requestId']}")
                    cur.execute(f"update generationRequests set status = '{json_status}' where requestId = {order['requestId']}")
                    cur.execute(f"update generationRequests set isDone = 1 where requestId = {order['requestId']}")
                    conn.commit()
            await asyncio.sleep(10)
    except Exception as e:
        print(e)
