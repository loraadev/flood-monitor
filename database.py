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
            risk_level TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_data(timestamp, city, rain_1h, humidity, description, risk_level):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weather_data (timestamp, city, rain_1h, humidity, description, risk_level)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, city, rain_1h, humidity, description, risk_level))
    conn.commit()
    conn.close()

def get_recent_data(limit=24):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, city, rain_1h, humidity, description, risk_level
        FROM weather_data
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows