import sqlite3


DATABASE = "habit_tracker.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    with open("schema.sql", "r") as file:
        connection.executescript(file.read())

    connection.commit()
    connection.close()