
import pymysql
import config
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
            '''[{'compId': 111, 'compGuid': '1eb47229-0499-11f0-9f77-0cc47a137a68', 'date1': datetime.date(2025, 3, 24), 'date2': datetime.date(2025, 4, 6), 'compName': 'Чемпионаты и Первенства России', 'city': 'Москва', 'regionId': 77, 'chairman_Id': '6887839538', 'scrutineerId': '834140698', 'gsName': 'Пермяков Вадим Евгеньевич', 'lin_const': 11, 'isActive': 0, 'isSecret': 1, 'generation_mode': 0, 'generation_zgs_mode': 0, 'generationRandomMode': 50, 'userId': 1, 'isPay': 0, 'pinCode': 5467}]'''

            for comp in competitions:
                compId = comp['compId']

                cur.execute(f"delete from competition_files where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition_group where compId = {compId}")
                conn.commit()

                cur.execute(f'select id from competition_group_crew where compId = {compId}')
                crew_ids = cur.fetchall()
                crew_ids = [i['id'] for i in crew_ids]
                '''[2077, 2078, 2079, 2080, 2081, 2082, 2083, 2084, 2085, 2086, 2087,]'''


                cur.execute(f"delete from competition_group_crew where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition_group_interdiction where compId = {compId}")
                conn.commit()

                cur.execute(f"select *  from competition_group_judges")
                ans = cur.fetchall()
                '''[{'id': 23878, 'crewId': 1967, 'typeId': 0, 'ident': 'A(1)', 'lastName': 'Ануфриева', 'firstName': 'Марина', 'judgeId': 4163, 'skateId': 27, 'floor': None}, {'id': 23879, 'crewId': 1967, 'typeId': 0, 'ident': 'B(2)', 'lastName': 'Беляк', 'firstName': 'Юлия', 'judgeId': 4167, 'skateId': 22, 'floor': None}, {'id': 23880, 'crewId': 1967, 'typeId': 0, 'ident': 'C(3)',]'''


                for jud in ans:
                    if jud['crewId'] in crew_ids:
                        cur.execute(f"delete from competition_group_judges where crewId = {jud['crewId']}")
                        conn.commit()


                cur.execute(f"delete from competition_judges where compId = {compId}")
                conn.commit()

                cur.execute(f"delete from competition where compId = {compId}")
                conn.commit()
                break


    except Exception as e:
        print(e)
        return -1


kill()
