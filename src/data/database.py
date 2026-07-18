import sqlite3

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