import os
from flask import Flask, render_template, jsonify, request
from database import create_table, get_recent_data
from collector import collect_data, get_forecast
from scheduler import start_scheduler
from analyzer import get_risk_color
from cities import CITIES, DEFAULT_CITY_SLUG, get_city

app = Flask(__name__)

create_table()
try:
    collect_data()
except Exception as e:
    print(f"Erro na coleta inicial: {e}")
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

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
