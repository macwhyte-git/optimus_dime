import sqlite3
from src.data.schema import SCHEMA

DATABASE = "data/trading_data.db"

class Database:

    def __init__(self):
        self.connection = sqlite3.connect(DATABASE)

    @property
    def conn(self):
        return self.connection

    def cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

    def create_tables(self):
        cursor = self.cursor()
        for sql_statement in SCHEMA:
            cursor.execute(sql_statement)
        self.commit()