import decimal
import os

import mysql.connector
from flask import Flask
from mysql.connector import errorcode
from mysql.connector.pooling import PooledMySQLConnection

import helpers.interfaces.database as interface_database
from .strava_goals import StatsType as strava_goals


class Database(interface_database.Database):
    host: str
    user: str
    password: str
    database: str
    port: int
    app: Flask
    cnx: PooledMySQLConnection

    def __init__(self, app: Flask):
        interface_database.Database.__init__(self, app)
        self.host = os.environ.get("MYSQL_HOST")
        self.user = os.environ.get("MYSQL_USER")
        self.password = os.environ.get("MYSQL_PASSWORD")
        self.database = os.environ.get("MYSQL_DATABASE")
        self.port = int(os.environ.get("MYSQL_PORT"))
        self.app = app
        if not self.database:
            self.app.config.logger.error("MYSQL_DATABASE environment variable not set")
            return
        if not self.host:
            self.app.config.logger.error("MYSQL_HOST environment variable not set")
            return
        if not self.port:
            self.app.config.logger.error("MYSQL_PORT environment variable not set")
            return
        if not self.user:
            self.app.config.logger.error("MYSQL_USER environment variable not set")
            return
        if not self.password:
            self.app.config.logger.error("MYSQL_PASSWORD environment variable not set")
            return

    def connect(self) -> bool:
        try:
            self.cnx = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci"
            )
            return True
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.app.config.logger.exception("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.app.config.logger.exception("Database does not exist")
            else:
                self.app.config.logger.exception(err)
            return False

    def load_token(self, athlete_id: int) -> dict | None:
        if not self.connect(): return None
        try:
            cursor = self.cnx.cursor()
            self.app.config.logger.info(
                f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(
                    athlete_id) + "")
            cursor.execute(f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(
                athlete_id) + "")
            result = cursor.fetchone()
            cursor.close()
            self.cnx.close()
            if result:
                return {"access_token": result[0], "refresh_token": result[1], "expires_at": str(result[2])}
            else:
                self.app.config.logger.error("No result.")
                return None
        except Exception as ex:
            self.app.config.logger.exception("Failed to load token." + str(ex))
            return None

    def save_token_cache(self, athlete_id, token_data) -> bool:
        if not self.connect(): return False
        try:
            cursor = self.cnx.cursor()
            cursor.execute(
                "REPLACE INTO token_cache (athlete_id, access_token, refresh_token, expires_at) VALUES (%s, %s, %s, %s)",
                (athlete_id, token_data['access_token'], token_data['refresh_token'], str(token_data['expires_at'])))

            self.cnx.commit()
            cursor.close()
            self.cnx.close()
            return True
        except Exception as ex:
            self.app.config.logger.exception("Failed to save token." + str(ex))
            return False

    def load_activities_cache(self, athlete_id) -> list:
        self.app.logger.info("loading info for athlete_id: " + str(athlete_id))
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            sql: str = "SELECT activity_id, athlete_id, name, distance, total_elevation_gain, type, sport_type, moving_time, start_date FROM activities WHERE athlete_id = " + str(
                athlete_id) + " ORDER BY start_date DESC"
            self.app.config.logger.info("RUNNING: " + sql)
            cursor.execute(sql)
            activities: list = []
            for row in cursor.fetchall():
                activities.append({
                    "activity_id": row[0],
                    "athlete_id": row[1],
                    "name": row[2],
                    "distance": row[3],
                    "total_elevation_gain": row[4],
                    "type": row[5],
                    "sport_type": row[6],
                    "moving_time": row[7],
                    "start_date": row[8],
                })
            cursor.close()
            self.cnx.close()
            return activities
        except Exception as ex:
            self.app.config.logger.exception("Failed to load activities." + str(ex))
            return []

    def load_strawalls(self, athlete_id) -> list:
        self.app.logger.info("loading info for athlete_id: " + str(athlete_id))
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            sql: str = "SELECT strawall_id, strawall_guid, name, width, height, active FROM strawalls WHERE athlete_id = " + str(
                athlete_id) + " ORDER BY name ASC"
            #self.app.config.logger.info("query: " + sql)
            cursor.execute(sql)
            strawalls: list = []
            for row in cursor.fetchall():
                strawalls.append({
                    "strawall_id": row[0],
                    "strawall_guid": row[1],
                    "name": row[2],
                    "width": row[3],
                    "height": row[4],
                    "active": row[5],
                })
            cursor.close()
            self.cnx.close()
            return strawalls
        except Exception as ex:
            self.app.config.logger.exception("Failed to load strawalls." + str(ex))
            return []

    def load_widgets_for_strawall(self, strawall_id) -> list:
        # self.app.logger.info("loading widgets for strawall: " + str(strawall_id))
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            sql: str = "SELECT `strawall_widget_id`, `name`, `width`, `height`, `top`, `left`, `type`, `props`, `active` FROM widgets WHERE strawall_guid = '" + str(strawall_id) + "' ORDER BY strawall_widget_id ASC"
            #self.app.config.logger.info("query: " + sql)
            cursor.execute(sql)
            strawalls_widgets: list = []
            for row in cursor.fetchall():
                print(row)
                strawalls_widgets.append({
                    "strawall_widget_id": row[0],
                    "name": row[1],
                    "width": row[2],
                    "height": row[3],
                    "top": row[4],
                    "left": row[5],
                    "type": row[6],
                    "props": row[7],
                    "active": row[8]
                })
            cursor.close()
            self.cnx.close()
            return strawalls_widgets
        except Exception as ex:
            self.app.config.logger.exception("Failed to load strawall widget." + str(ex))
            return []


    def save_activities_cache(self, athlete_id, activities):
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            # cursor.execute("DELETE FROM activities WHERE athlete_id = " + str(athlete_id) + "" )
            for activity in activities:
                # self.app.config.logger.warning(activity)
                cursor.execute(
                    "INSERT INTO activities (activity_id, athlete_id, name, distance, total_elevation_gain, type, sport_type, moving_time, start_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (activity['activity_id'],
                     activity['athlete_id'],
                     activity['name'],
                     activity['distance'],
                     activity['total_elevation_gain'],
                     activity['type'],
                     activity['sport_type'],
                     activity['moving_time'],
                     activity['start_date'])
                )
            self.cnx.commit()
            cursor.close()
            self.cnx.close()
            return activities
        except Exception as ex:
            self.app.config.logger.exception("Failed to save activities." + str(ex))
            return []

    def load_athlete_stats(self, athlete_id: int) -> dict|None:
        if not self.connect(): return None
        try:
            cursor = self.cnx.cursor()
            sql: str = """SELECT
                            gp.athlete_id,
                            gp.goal_name,
                            gp.plan,
                            gs.stat
                        FROM
                            goals_plans gp
                        INNER JOIN
                            goals_stats gs
                        ON
                            gp.athlete_id = gs.athlete_id
                            AND gp.goal_name = gs.goal_name
                        WHERE
                            gp.athlete_id = %d AND gp.plan is not null
                        """ % athlete_id
            #self.app.config.logger.info("query sql: " + sql)
            cursor.execute(sql)

            column_names = [desc[0] for desc in cursor.description]
            athlete_stats = {}

            for row in cursor.fetchall():
                row_dict = dict(zip(column_names, row))
                strava_goal: dict = strava_goals[row_dict['goal_name']].value # get meta info on goal
                athlete_stats[row_dict['goal_name']] = {
                    "name": strava_goal['name'],
                    "plan": str(round(number=row_dict["plan"]/strava_goal['scale'], ndigits=0)),
                    "stat": str(round(number=row_dict["stat"]/strava_goal['scale'], ndigits=strava_goal['decimal']))
                }
            cursor.close()
            self.cnx.close()
            return athlete_stats
        except Exception as ex:
            self.app.config.logger.exception("Failed to load activities." + str(ex))
            return None

    def save_athlete_stats(self, athlete_id: int, goals: dict = None) -> bool:
        if not self.connect():
            return False
        try:
            # todo read current plan and scopes! Map them
            # read from this table
            self.app.config.logger.debug("Saving athlete_stats.")
            # cursor = self.cnx.cursor()
            # query = "UPDATE athletes SET ytd_ride_current = %s, ytd_ride_elev_current = %s WHERE athlete_id = %s"
            # cursor.execute(query, (ytd_ride_current, ytd_ride_elev_current, athlete_id))
            # self.cnx.commit()

            self.app.config.logger.debug("clearing current stats ...")
            cursor = self.cnx.cursor()
            query = "DELETE FROM goals_stats WHERE athlete_id = " + str(athlete_id)
            cursor.execute(query)
            self.cnx.commit()

            cursor = self.cnx.cursor()
            goal_queries = []
            for key, value in goals.items():
                goal_queries.append((athlete_id, key, round(value, 2)))
            insert_query = "INSERT INTO goals_stats (athlete_id, goal_name, stat) VALUES (%s, %s, %s)"
            self.app.config.logger.debug("inserting current stats ...")
            cursor.executemany(insert_query, goal_queries)
            self.cnx.commit()
            cursor.close()
            self.cnx.close()
            self.app.config.logger.info("New athlete stats saved.")
            return True

        except Exception as ex:
            self.app.config.logger.exception("Failed to save athlete stats. " + str(ex))
            return False
