import sqlite3
from datetime import datetime

DB_NAME = 'Events.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # чтобы результаты были как словари
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ---- Операции с пользователями (минимум для авторизации) ----

def create_user(username, email, password_hash):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        return cursor.lastrowid  # возвращает id нового пользователя

def get_user_by_email(email):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

def create_event(user_id, title, event_date, description=None, location=None, image_url=None, notification_enabled=False, notification_time=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events 
            (user_id, title, event_date, description, location, image_url, notification_enabled, notification_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, event_date, description, location, image_url, notification_enabled, notification_time))
        return cursor.lastrowid

def get_all_events():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY event_date")
        return cursor.fetchall()

def get_events_by_user(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY event_date", (user_id,))
        return cursor.fetchall()

def get_event_by_id(event_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        return cursor.fetchone()

def update_event(event_id, **kwargs):
    allowed_fields = ['title', 'event_date', 'description', 'location', 'image_url', 'notification_enabled', 'notification_time']
    set_clauses = []
    values = []
    for field, value in kwargs.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ?")
            values.append(value)
    if not set_clauses:
        return False
    values.append(event_id)
    query = f"UPDATE events SET {', '.join(set_clauses)} WHERE id = ?"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        return cursor.rowcount > 0  # сколько строк обновлено

def delete_event(event_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cursor.rowcount > 0

# операции с праздниками

def add_holiday(name, date, description):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO holidays (name, date, description) VALUES (?, ?, ?)", (name, date, description))
        return cursor.lastrowid

def get_all_holidays():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM holidays ORDER BY date")
        return cursor.fetchall()

#####################################################################################

if __name__ == "__main__":
    print("Демонстрационная проба работы с бд")

    # Добавляем тестового пользователя (пароль вероятно хэшируется, сейчас просто текст)
    user_id = create_user("nikita", "nikita@mail.ru", "password")
    print(f"Создан пользователь с id = {user_id}")

    # Добавляем несколько событий
    event1_id = create_event(
        user_id = user_id,
        title = "Проверка связи",
        event_date = datetime(2026, 4, 10, 14, 0, 0),
        description = "Обсуждение",
        location = "Авиамоторная",
        notification_enabled = True,
        notification_time = datetime(2026, 4, 10, 13, 0, 0)
    )
    print(f"Создано событие 1, id = {event1_id}")

    event2_id = create_event(
        user_id = user_id,
        title = "отчёт",
        event_date = datetime(2026, 4, 10, 18, 0, 0),
        description = "Проверить",
        location = "Онлайн"
    )
    print(f"Создано событие 2, id = {event2_id}")

    # Получить список всех событий
    all_events = get_all_events()
    print("\nВсе события:")
    for e in all_events:
        print(f" {e['id']}: {e['title']} - {e['event_date']}")

    # Получить события пользователя
    user_events = get_events_by_user(user_id)
    print(f"\nСобытия пробного пользователя:")
    for e in user_events:
        print(f"  {e['title']} на {e['event_date']}")

    # Обновить событие (изменить заголовок)
    success = update_event(event2_id, title="Изменение", description="Провека изменения")
    print(f"\nОбновление события {event2_id}: {'успешно' if success else 'не удалось'}")

    # Проверить обновление
    updated_event = get_event_by_id(event2_id)
    print(f"После обновления: {updated_event['title']} - {updated_event['description']}")

    # Удалить событие
    delete_event(event1_id)
    print(f"\nУдаление события {event1_id}")

    # Проверить остаток
    remaining = get_all_events()
    print(f"Сколько осталось событий: {len(remaining)}")

    # Тестовый праздник 
    holiday_id = add_holiday("День программиста", "2026-09-13", "праздник")
    print(f"\nДобавлен праздник: id = {holiday_id}")

    holidays = get_all_holidays()
    print("Список праздников:")
    for h in holidays:
        print(f"  {h['name']} - {h['date']}")

    print("\nТакая демонстрация")