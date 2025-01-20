import os

import mysql.connector
from flask import Flask
from mysql.connector import errorcode
from mysql.connector.pooling import PooledMySQLConnection

import helpers.interfaces.database as interface_database


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
            self.app.logger.error("MYSQL_DATABASE environment variable not set")
            return
        if not self.host:
            self.app.logger.error("MYSQL_HOST environment variable not set")
            return
        if not self.port:
            self.app.logger.error("MYSQL_PORT environment variable not set")
            return
        if not self.user:
            self.app.logger.error("MYSQL_USER environment variable not set")
            return
        if not self.password:
            self.app.logger.error("MYSQL_PASSWORD environment variable not set")
            return

    def connect(self) -> bool:
        try:
            self.cnx = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            return True
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.app.logger.exception("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.app.logger.exception("Database does not exist")
            else:
                self.app.logger.exception(err)
            return False

    def load_token(self, athlete_id: int) -> dict | None:
        if not self.connect(): return None
        try:
            cursor = self.cnx.cursor()
            self.app.logger.warning(
                f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(
                    athlete_id) + "")
            cursor.execute(f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(
                athlete_id) + "")
            result = cursor.fetchone()
            cursor.close()
            self.cnx.close()
            if result:
                self.app.logger.warning("returned: " + str(result))
                self.app.logger.warning("returned[2]: " + str(result[2]))
                return {"access_token": result[0], "refresh_token": result[1], "expires_at": str(result[2])}
            else:
                self.app.logger.warning("No result.")
                return None
        except Exception as ex:
            self.app.logger.exception("Failed to load token." + str(ex))
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
            self.app.logger.exception("Failed to save token." + str(ex))
            return False

    def load_activities_cache(self, athlete_id) -> list:
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            sql: str = "SELECT activity_id, athlete_id, name, distance, type, sport_type, moving_time, start_date FROM activities WHERE athlete_id = " + str(
                athlete_id) + " ORDER BY start_date DESC"
            self.app.logger.warning("RUNNING: " + sql)
            cursor.execute(sql)
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "activity_id": row[0],
                    "athlete_id": row[1],
                    "name": row[2],
                    "distance": row[3],
                    "type": row[4],
                    "sport_type": row[5],
                    "moving_time": row[6],
                    "start_date": row[7],
                })
            cursor.close()
            self.cnx.close()
            return activities
        except Exception as ex:
            self.app.logger.exception("Failed to load activities." + str(ex))
            return []

    def save_activities_cache(self, athlete_id, activities):
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            # cursor.execute("DELETE FROM activities WHERE athlete_id = " + str(athlete_id) + "" )
            for activity in activities:
                # self.app.logger.warning(activity)
                cursor.execute(
                    "INSERT INTO activities (activity_id, athlete_id, name, distance, type, sport_type, moving_time, start_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (activity['activity_id'],
                     activity['athlete_id'],
                     activity['name'],
                     activity['distance'],
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
            self.app.logger.exception("Failed to save activities." + str(ex))
            return []

    def load_profile(self, athlete_id) -> dict | None:
        if not self.connect(): return []
        try:
            cursor = self.cnx.cursor()
            cursor.execute(
                "SELECT ytd_ride, ytd_run, ytd_swim FROM athletes WHERE athlete_id = " + str(athlete_id) + "")
            result = cursor.fetchone()
            cursor.close()
            self.cnx.close()
            if result:
                self.app.logger.warning("returned: " + str(result))
                self.app.logger.warning("returned[2]: " + str(result[2]))
                self.app.logger.warning('loaded: ' + str(result))
                return {"ytd_ride": int(result[0]), "ytd_run": int(result[1]), "ytd_swim": int(result[2])}
            else:
                self.app.logger.warning("No result.")
                return None

        except Exception as ex:
            self.app.logger.exception("Failed to load profile." + str(ex))
            return []
