import requests
from datetime import datetime, timezone, timedelta
from database import create_table, insert_data
from analyzer import analyze_risk

CITY = "Osvaldo Cruz"
LATITUDE = -21.79667
LONGITUDE = -50.87861
URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "current": "precipitation,relative_humidity_2m,wind_speed_10m,weather_code",
    "hourly": "precipitation,precipitation_probability",
    "timezone": "America/Sao_Paulo"
}

# Códigos de tempo WMO usados pela Open-Meteo
WEATHER_CODES = {
    0: "Céu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina com geada",
    51: "Garoa fraca",
    53: "Garoa moderada",
    55: "Garoa intensa",
    56: "Garoa congelante fraca",
    57: "Garoa congelante intensa",
    61: "Chuva fraca",
    63: "Chuva moderada",
    65: "Chuva forte",
    66: "Chuva congelante fraca",
    67: "Chuva congelante forte",
    71: "Neve fraca",
    73: "Neve moderada",
    75: "Neve forte",
    77: "Grãos de neve",
    80: "Pancadas de chuva fracas",
    81: "Pancadas de chuva moderadas",
    82: "Pancadas de chuva violentas",
    85: "Pancadas de neve fracas",
    86: "Pancadas de neve fortes",
    95: "Trovoada",
    96: "Trovoada com granizo fraco",
    99: "Trovoada com granizo forte"
}

fuso_brasilia = timezone(timedelta(hours=-3))

def describe_weather(code):
    return WEATHER_CODES.get(code, "Desconhecido")

def fetch_weather():
    response = requests.get(URL, params=PARAMS, timeout=10)
    data = response.json()
    if response.status_code != 200:
        raise RuntimeError(f"Erro na API: {data.get('reason', 'desconhecido')}")
    return data

def collect_data():
    try:
        data = fetch_weather()
        current = data["current"]
        rain_1h = current.get("precipitation") or 0
        humidity = current.get("relative_humidity_2m")
        wind_speed = current.get("wind_speed_10m")
        description = describe_weather(current.get("weather_code"))
        timestamp = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M")
        risk_level = analyze_risk(rain_1h)
        create_table()
        insert_data(timestamp, CITY, rain_1h, humidity, description, risk_level, wind_speed)
        print(f"[{timestamp}] Coletado: chuva={rain_1h}mm/h | umidade={humidity}% | vento={wind_speed}km/h | risco={risk_level}")
    except Exception as e:
        print(f"Erro ao coletar dados: {e}")

def get_forecast(max_hours=12):
    data = fetch_weather()
    hourly = data["hourly"]
    now = datetime.now(fuso_brasilia)
    forecast = []
    for time, precipitation, probability in zip(
        hourly["time"], hourly["precipitation"], hourly["precipitation_probability"]
    ):
        # Os horários vêm no fuso de America/Sao_Paulo; descarta os que já passaram
        if datetime.fromisoformat(time).replace(tzinfo=fuso_brasilia) <= now:
            continue
        if len(forecast) >= max_hours:
            break
        forecast.append({
            "time": time,
            "precipitation": precipitation,
            "precipitation_probability": probability
        })
    return forecast

if __name__ == "__main__":
    collect_data()
