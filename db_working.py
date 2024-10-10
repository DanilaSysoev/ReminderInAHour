import os
import sqlite3
from datetime import timedelta


def _create_user_id_chat_id(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ChatId (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL
        );
    """)

    
def _create_titles(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Title (
            user_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL
        );
    """)

    
def _create_messages(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Message (
            user_id INTEGER PRIMARY KEY,
            message TEXT NOT NULL
        );
    """)


def _create_reminders(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Reminder (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            dete_time TEXT NOT NULL
            );
    """)
    
    
def _create_state(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS State (
        user_id INTEGER PRIMARY KEY,
        state INTEGER NOT NULL
        );
    """)
    

def create_database(db_name):
    global _database
    _database = db_name
    if os.path.exists(db_name):
        return
    conn = sqlite3.connect(db_name)
    
    _create_user_id_chat_id(conn)
    _create_titles(conn)
    _create_messages(conn)
    _create_reminders(conn)
    _create_state(conn)
    
    conn.commit()
    conn.close()


def get_state(user_id):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM State WHERE user_id = ?;", (user_id,))
    state = cursor.fetchone()
    conn.close()
    if state is None:
        return -1
    return state[0]


def set_state(user_id, state):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO State VALUES (?, ?);", (user_id, state))
    conn.commit()
    conn.close()


def get_chat_id(user_id):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM ChatId WHERE user_id = ?;", (user_id,))
    chat_id = cursor.fetchone()
    conn.close()
    if chat_id is None:
        return -1
    return chat_id[0]


def set_chat_id(user_id, chat_id):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO ChatId VALUES (?, ?);", (user_id, chat_id))
    conn.commit()
    conn.close()
    
    
def get_title(user_id):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM Title WHERE user_id = ?;", (user_id,))
    title = cursor.fetchone()
    conn.close()
    if title is None:
        return ''
    return title[0]


def set_title(user_id, title):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO Title VALUES (?, ?);", (user_id, title))
    conn.commit()
    conn.close()


def get_message(user_id):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM Message WHERE user_id = ?;", (user_id,))
    message = cursor.fetchone()
    conn.close()
    if message is None:
        return ''
    return message[0]


def set_message(user_id, message):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO Message VALUES (?, ?);", (user_id, message))
    conn.commit()
    conn.close()


def get_reminder_on_date(user_id, dete):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT * FROM Reminder
           WHERE user_id = ? AND dete_time >= ? AND dete_time < ?;''',
           (user_id, dete, dete + timedelta(days=1))
    )
    return sorted(cursor.fetchall(), key=lambda x: x[4])
    

def remove_reminder_earlier(dete_time):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute('''
            DELETE FROM Reminder
            WHERE dete_time <= ?;
        ''',
        (dete_time,)
    )
    conn.commit()
    conn.close()


def get_reminders_earlier(date_time):
    conn = sqlite3.connect(_database)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM Reminder
        WHERE dete_time <= ?;
    ''', (date_time,))
    return cursor.fetchall()


def add_reminder(user_id, title, message, dete_time):
    conn = sqlite3.connect(_database)
    conn.execute('INSERT INTO Reminder (user_id, title, message, dete_time) VALUES (?, ?, ?, ?);', (user_id, title, message, dete_time))
    conn.commit()
    conn.close()


_database = 'database.db'