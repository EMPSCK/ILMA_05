import pymysql
import config
import asyncio
import os
import requests
from config import updatetime
from chairman_moves import generation_logic

async def checkGenerationOrders():
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
            cur.execute(f"select * from generationRequests")
            results = cur.fetchall()
            if len(results) == 0:
                return 1

            for order in results:
                compId = order['compId']
                regionId = order['regionId']
                groupList = list(map(int, order['groupNumbers'].split(';')))

                data = {'compId': compId, "regionId": regionId, "status": 12, "groupList": groupList}
                text, json = await generation_logic.get_ans(data)
                print(json)
    except:
        return -1

loop = asyncio.get_event_loop()
forecast = loop.run_until_complete(checkGenerationOrders())
loop.close()
