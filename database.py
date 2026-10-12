import sqlite3

def get_connection():
    conn = sqlite3.connect("flood_data.db")
    return conn

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            rain_1h REAL DEFAULT 0,
            humidity INTEGER,
            description TEXT,
            risk_level TEXT,
            wind_speed REAL
        )
    """)
    # Bancos criados antes da coluna wind_speed: adiciona sem apagar o histórico
    cursor.execute("PRAGMA table_info(weather_data)")
    columns = [column[1] for column in cursor.fetchall()]
    if "wind_speed" not in columns:
        cursor.execute("ALTER TABLE weather_data ADD COLUMN wind_speed REAL")
    # Último nível de alerta notificado por cidade
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_state (
            city TEXT PRIMARY KEY,
            last_level TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_data(timestamp, city, rain_1h, humidity, description, risk_level, wind_speed=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weather_data (timestamp, city, rain_1h, humidity, description, risk_level, wind_speed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, city, rain_1h, humidity, description, risk_level, wind_speed))
    conn.commit()
    conn.close()

def get_recent_data(limit=24, city=None):
    conn = get_connection()
    cursor = conn.cursor()
    if city is None:
        cursor.execute("""
            SELECT timestamp, city, rain_1h, humidity, description, risk_level, wind_speed
            FROM weather_data
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT timestamp, city, rain_1h, humidity, description, risk_level, wind_speed
            FROM weather_data
            WHERE city = ?
            ORDER BY id DESC
            LIMIT ?
        """, (city, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_rain_readings(city, limit=200):
    # Leituras (timestamp, chuva) da cidade, da mais antiga para a mais recente
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, rain_1h
        FROM weather_data
        WHERE city = ?
        ORDER BY id DESC
        LIMIT ?
    """, (city, limit))
    rows = cursor.fetchall()
    conn.close()
    rows.reverse()
    return rows

def get_alert_level(city):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_level FROM alert_state WHERE city = ?", (city,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Normal"

def set_alert_level(city, level, updated_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alert_state (city, last_level, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(city) DO UPDATE SET last_level = excluded.last_level, updated_at = excluded.updated_at
    """, (city, level, updated_at))
    conn.commit()
    conn.close()

def reset_alert_levels(cities):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM alert_state WHERE city = ?", [(city,) for city in cities])
    conn.commit()
    conn.close()
