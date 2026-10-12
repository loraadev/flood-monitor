import os
from flask import Flask, render_template, jsonify, request
from database import create_table, get_recent_data
from collector import get_forecast
from scheduler import start_scheduler
from analyzer import get_risk_color
from cities import CITIES, DEFAULT_CITY_SLUG, get_city
from telegram_bot import WEBHOOK_PATH, check_webhook_secret, handle_update, update_chat_id
from ratelimit import RateLimiter

app = Flask(__name__)

create_table()
# A coleta inicial roda em segundo plano pelo agendador (ver scheduler.py)
start_scheduler()

def selected_city():
    slug = request.args.get("city", DEFAULT_CITY_SLUG)
    return get_city(slug)

def city_not_found():
    return jsonify({"error": "Cidade desconhecida"}), 400

@app.route("/")
def index():
    return render_template("index.html", default_city=DEFAULT_CITY_SLUG)

@app.route("/api/cities")
def api_cities():
    return jsonify(CITIES)

@app.route("/api/data")
def api_data():
    city = selected_city()
    if city is None:
        return city_not_found()
    rows = get_recent_data(24, city["name"])
    data = []
    for row in rows:
        data.append({
            "timestamp": row[0],
            "city": row[1],
            "rain_1h": row[2],
            "humidity": row[3],
            "description": row[4],
            "risk_level": row[5],
            "color": get_risk_color(row[5]),
            "wind_speed": row[6]
        })
    return jsonify(data)

@app.route("/api/latest")
def api_latest():
    city = selected_city()
    if city is None:
        return city_not_found()
    rows = get_recent_data(1, city["name"])
    if not rows:
        return jsonify({
            "timestamp": "--",
            "city": city["name"],
            "rain_1h": 0,
            "humidity": 0,
            "description": "--",
            "risk_level": "Normal",
            "color": "#28a745",
            "wind_speed": 0
        })
    row = rows[0]
    return jsonify({
        "timestamp": row[0],
        "city": row[1],
        "rain_1h": row[2],
        "humidity": row[3],
        "description": row[4],
        "risk_level": row[5],
        "color": get_risk_color(row[5]),
        "wind_speed": row[6]
    })

@app.route("/api/forecast")
def api_forecast():
    city = selected_city()
    if city is None:
        return city_not_found()
    try:
        return jsonify(get_forecast(city))
    except Exception as e:
        print(f"Erro ao buscar previsão de {city['name']}: {e}")
        return jsonify({"error": "Não foi possível obter a previsão"}), 502

# Webhook do Telegram: só existe com TELEGRAM_WEBHOOK_SECRET definido.
# O caminho é derivado do segredo e toda chamada precisa trazer o segredo
# no cabeçalho X-Telegram-Bot-Api-Secret-Token.
#
# Limites de taxa (em memória, por processo):
# - Por chat: 20 mensagens/minuto. Uso normal (/start, escolher cidade,
#   /status, /parar) fica bem abaixo disso. Acima do limite a mensagem é
#   descartada com 200: com qualquer outro código o Telegram reenviaria a
#   mesma mensagem e ela acabaria processada depois.
# - Por IP, só para chamadas SEM o segredo válido: 10/minuto, depois 429.
#   Não se aplica às mensagens verdadeiras porque todas chegam dos
#   servidores do Telegram (o limite por IP somaria todos os usuários).
CHAT_LIMIT_PER_MINUTE = 20
INVALID_IP_LIMIT_PER_MINUTE = 10
chat_limiter = RateLimiter(CHAT_LIMIT_PER_MINUTE, 60)
invalid_ip_limiter = RateLimiter(INVALID_IP_LIMIT_PER_MINUTE, 60)
limit_log_limiter = RateLimiter(1, 60)  # no máximo um aviso por minuto por origem no log

def client_ip():
    # No Render a conexão chega por proxy; o último IP do X-Forwarded-For é o
    # que o proxy viu. Serve só para o limite de chamadas inválidas.
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[-1].strip() or request.remote_addr or "desconhecido"

if WEBHOOK_PATH:
    @app.route(WEBHOOK_PATH, methods=["POST"])
    def telegram_webhook():
        if not check_webhook_secret(request.headers.get("X-Telegram-Bot-Api-Secret-Token")):
            ip = client_ip()
            if not invalid_ip_limiter.allow(ip):
                if limit_log_limiter.allow("ip:" + ip):
                    print("Telegram: excesso de chamadas sem segredo válido; respondendo 429")
                return "", 429
            return "", 403
        if (request.content_length or 0) > 100_000:
            return "", 413
        try:
            update = request.get_json(silent=True)
            chat_id = update_chat_id(update)
            if chat_id is not None and not chat_limiter.allow(chat_id):
                if limit_log_limiter.allow(chat_id):
                    print(f"Telegram: um chat passou de {CHAT_LIMIT_PER_MINUTE} mensagens/minuto; mensagens descartadas")
                return "", 200
            handle_update(update)
        except Exception as e:
            print(f"Erro ao tratar mensagem do Telegram: {type(e).__name__}")
        # Responde 200 mesmo com erro interno para o Telegram não reenviar a mesma mensagem
        return "", 200
else:
    print("Telegram: TELEGRAM_WEBHOOK_SECRET não configurado; webhook desativado.")

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
