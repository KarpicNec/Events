import sqlite3
from datetime import datetime

DB_NAME = 'Events.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# операции с пользователями 

def get_user_by_username(username: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def get_user_by_id(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

def create_user(username: str, email: str, password_hash: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

def promote_to_admin(user_id: int):
	with get_connection() as conn:
		cursor = conn.cursor()
		cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
		return cursor.rowcount > 0	

# операции с событиями

def create_event(user_id, title, event_date, description=None, location=None, image_url=None, notification_enabled=False, notification_time=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events
            (user_id, title, event_date, description, location, image_url, notification_enabled, notification_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, event_date, description, location, image_url, notification_enabled, notification_time))
        return cursor.lastrowid

def get_events_by_user(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY event_date", (user_id,))
        return cursor.fetchall()

def get_event_by_id(event_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        return cursor.fetchone()

def update_event(event_id: int, **kwargs):
    allowed_fields = ['title', 'event_date', 'description', 'location', 'image_url', 'notification_enabled', 'notification_time']
    set_clauses = []
    values = []
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            set_clauses.append(f"{field} = ?")
            values.append(value)
    if not set_clauses:
        return False
    values.append(event_id)
    query = f"UPDATE events SET {', '.join(set_clauses)} WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        return cursor.rowcount > 0

def delete_event(event_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cursor.rowcount > 0

def get_all_events():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY event_date")
        return cursor.fetchall()

# операции с праздниками

def add_holiday(name: str, date: str, description: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO holidays (name, date, description) VALUES (?, ?, ?)", (name, date, description))
        return cursor.lastrowid

def get_all_holidays():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM holidays ORDER BY date")
        return cursor.fetchall()

def delete_holiday(holiday_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))
        return cursor.rowcount > 0