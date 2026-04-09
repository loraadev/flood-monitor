import requests
from datetime import datetime
from database import create_table, insert_data
from analyzer import analyze_risk

API_KEY = "9003d68f338e20cf98df1ee527c17340"
CITY = "Osvaldo Cruz,BR"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=pt_br"

def collect_data():
    try:
        response = requests.get(URL)
        data = response.json()

        if response.status_code != 200:
            print(f"Erro na API: {data.get('message', 'desconhecido')}")
            return

        rain_1h = 0
        if "rain" in data:
            rain_1h = data["rain"].get("1h", 0)

        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        risk_level = analyze_risk(rain_1h)

        create_table()
        insert_data(timestamp, CITY, rain_1h, humidity, description, risk_level)

        print(f"[{timestamp}] Coletado: chuva={rain_1h}mm/h | umidade={humidity}% | risco={risk_level}")

    except Exception as e:
        print(f"Erro ao coletar dados: {e}")

if __name__ == "__main__":
    collect_data()