from logging import Logger

from flask import Flask


class Database:
    log: Logger
    def __init__(self, app: Flask):
        self.logger = app.logger
        self.logger.debug("database")
        pass

    def load_token(self, athlete_id: str) -> dict:
        pass

    def save_token_cache(self, athlete_id, token_data) -> bool:
        pass

    def load_athlete(self, athlete_id: int) -> dict:
        pass