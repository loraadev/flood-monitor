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
