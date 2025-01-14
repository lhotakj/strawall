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
            self.app.logger.warning(f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(athlete_id) + "")
            cursor.execute(f"SELECT access_token, refresh_token, expires_at FROM token_cache WHERE athlete_id = " + str(athlete_id) + "")
            result = cursor.fetchone()
            cursor.close()
            self.cnx.close()
            if result:
                return {"access_token": result[0], "refresh_token": result[1], "expires_at": result[2]}
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
                (athlete_id, token_data['access_token'], token_data['refresh_token'], token_data['expires_at']))

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
            cursor.execute("SELECT activity_id, name, distance, moving_time, start_date FROM activities_cache WHERE athlete_id = %s", (athlete_id,))
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    "id": row[0],
                    "name": row[1],
                    "distance": row[2],
                    "moving_time": row[3],
                    "start_date": row[4],
                })
            cursor.close()
            self.cnx.close()
            return activities
        except Exception as ex:
            self.app.logger.exception("Failed to load activities." + str(ex))
            return []
