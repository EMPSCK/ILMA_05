import pymysql
import json
import requests
import config
from queries import chairman_queries_02

async def update_judges_list():
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
            cur.execute(f"DELETE FROM judges")
            conn.commit()

            url = 'https://dance.vftsarr.ru/api/get.php'
            get_params = {'login': 'skatingsystem', 'password': '0987654321', 'data': '{"What":"Judges"}'}
            response = requests.get(url, get_params)
            f = json.loads(response.text)
        

            for jud in f:
                name = jud['FirstName'].strip()
                sex = await chairman_queries_02.get_gender(name)
                if sex is None:
                    sql = "INSERT INTO gender_unknown (`lastName`, `firstName`, `secondName`) VALUES (%s, %s, %s)"
                    cur.execute(sql,
                                (jud['LastName'], jud['FirstName'], jud['SecondName']))
                    conn.commit()


                sql = "INSERT INTO judges (`BookNumber`, `LastName`, `FirstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `Archive`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `gender`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (jud['BookNumber'], jud['LastName'], jud['FirstName'], jud['SecondName'], jud['Birth'],
                                  jud['DSFARR_Category'], jud['DSFARR_CategoryDate'], jud['WDSF_CategoryDate'],
                                  jud['RegionId'], jud['City'], jud['Club'], jud['Translit'], jud['Archive'],
                                  jud['SPORT_Category'], jud['SPORT_CategoryDate'], jud['SPORT_CategoryDateConfirm'], 'ftsarr', sex))
                conn.commit()
            cur.close()
        return 1
    except Exception as e:
        print(e)
        return 0
