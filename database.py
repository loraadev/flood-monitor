import sqlite3

NEW_COLUMNS = [
    ("wind_speed", "REAL"),
    # Origem do registro: "oficial" (Open-Meteo); futuramente, o sensor físico
    ("origem_dado", "TEXT"),
    # Dados futuros do sensor físico (ficam nulos por enquanto)
    ("id_dispositivo", "TEXT"),
    ("ponto_instalacao", "TEXT"),
    ("co2_ppm", "REAL"),
    ("pm1_0", "REAL"),
    ("pm2_5", "REAL"),
    ("pm10", "REAL"),
    ("temperatura_sensor", "REAL"),
    ("umidade_sensor", "REAL"),
    ("status_conexao", "TEXT")
]

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
    # Colunas adicionadas depois da criação da tabela: entram em bancos
    # antigos sem apagar o histórico, e só se ainda não existirem
    cursor.execute("PRAGMA table_info(weather_data)")
    columns = [column[1] for column in cursor.fetchall()]
    for name, sql_type in NEW_COLUMNS:
        if name not in columns:
            cursor.execute(f"ALTER TABLE weather_data ADD COLUMN {name} {sql_type}")
            if name == "origem_dado":
                # Todo o histórico existente veio da API meteorológica oficial
                cursor.execute("UPDATE weather_data SET origem_dado = 'oficial' WHERE origem_dado IS NULL")
    # Último nível de alerta notificado por cidade
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_state (
            city TEXT PRIMARY KEY,
            last_level TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    # Inscritos do Telegram: um chat pode acompanhar várias cidades (slug)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER NOT NULL,
            city TEXT NOT NULL,
            created_at TEXT,
            PRIMARY KEY (chat_id, city)
        )
    """)
    conn.commit()
    conn.close()

def insert_data(timestamp, city, rain_1h, humidity, description, risk_level, wind_speed=None, origem_dado=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weather_data (timestamp, city, rain_1h, humidity, description, risk_level, wind_speed, origem_dado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, city, rain_1h, humidity, description, risk_level, wind_speed, origem_dado))
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

def add_subscriber(chat_id, city, created_at):
    # Devolve True se a inscrição é nova, False se já existia
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO subscribers (chat_id, city, created_at)
        VALUES (?, ?, ?)
    """, (chat_id, city, created_at))
    added = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return added

def get_subscriptions(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city FROM subscribers WHERE chat_id = ? ORDER BY rowid", (chat_id,))
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

def get_subscribers(city):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers WHERE city = ?", (city,))
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

def remove_subscription(chat_id, city=None):
    # Sem cidade, remove todas as inscrições do chat
    conn = get_connection()
    cursor = conn.cursor()
    if city is None:
        cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    else:
        cursor.execute("DELETE FROM subscribers WHERE chat_id = ? AND city = ?", (chat_id, city))
    removed = cursor.rowcount
    conn.commit()
    conn.close()
    return removed

def reset_alert_levels(cities):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM alert_state WHERE city = ?", [(city,) for city in cities])
    conn.commit()
    conn.close()
