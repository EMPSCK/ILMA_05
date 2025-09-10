import config
import pymysql
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


kill()
