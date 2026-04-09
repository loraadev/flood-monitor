from flask import Flask, render_template, jsonify
from database import create_table, get_recent_data
from collector import collect_data
from scheduler import start_scheduler
from analyzer import get_risk_color

app = Flask(__name__)

create_table()
collect_data()
start_scheduler()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    rows = get_recent_data(24)
    data = []
    for row in rows:
        data.append({
            "timestamp": row[0],
            "city": row[1],
            "rain_1h": row[2],
            "humidity": row[3],
            "description": row[4],
            "risk_level": row[5],
            "color": get_risk_color(row[5])
        })
    return jsonify(data)

@app.route("/api/latest")
def api_latest():
    rows = get_recent_data(1)
    if not rows:
        return jsonify({
            "timestamp": "--",
            "city": "--",
            "rain_1h": 0,
            "humidity": 0,
            "description": "--",
            "risk_level": "Normal",
            "color": "#28a745"
        })
    row = rows[0]
    return jsonify({
        "timestamp": row[0],
        "city": row[1],
        "rain_1h": row[2],
        "humidity": row[3],
        "description": row[4],
        "risk_level": row[5],
        "color": get_risk_color(row[5])
    })

if __name__ == "__main__":
    app.run(debug=True)