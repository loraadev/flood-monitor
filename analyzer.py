from datetime import timedelta

def analyze_risk(rain_1h):
    if rain_1h is None:
        rain_1h = 0

    if rain_1h < 5:
        return "Normal"
    elif rain_1h <= 25:
        return "Atenção"
    else:
        return "Alerta Vermelho"

def get_risk_color(risk_level):
    colors = {
        "Normal": "#28a745",
        "Atenção": "#ffc107",
        "Alerta Vermelho": "#dc3545"
    }
    return colors.get(risk_level, "#28a745")


# =====================================================================
# LIMIARES DE ALERTA — edite aqui
# ---------------------------------------------------------------------
# Base: critérios de aviso do INMET (chuva acumulada em 24h e vento) e
# gatilho de chuva horária do Alerta Rio (25 mm/h e 50 mm/h).
# Não existe um número nacional fixo para janelas curtas (1h / 3h): os
# valores de chuva atual e de previsão em 1h/3h abaixo são uma escolha do
# projeto inspirada no Alerta Rio e podem ser ajustados à realidade local.
# Um nível dispara se QUALQUER um dos critérios dele for atingido (>=).
# =====================================================================
ALERT_THRESHOLDS = {
    "Atenção": {
        "rain_now_mm_h": 25,       # chuva medida agora (mm/h)
        "forecast_1h_mm": 25,      # chuva prevista em qualquer 1 hora (mm)
        "accumulated_24h_mm": 50,  # chuva acumulada nas últimas 24h (mm)
        "wind_km_h": 50            # vento medido agora (km/h)
    },
    "Alerta Vermelho": {
        "rain_now_mm_h": 50,
        "forecast_3h_mm": 50,      # chuva prevista em qualquer janela de 3 horas seguidas (mm)
        "accumulated_24h_mm": 100,
        "wind_km_h": 90
    }
}

# Tempo máximo que uma leitura conta no acúmulo de 24h. Evita que uma
# leitura de chuva "valha" por horas quando o servidor ficou parado.
MAX_READING_HOURS = 1

LEVEL_ORDER = {"Normal": 0, "Atenção": 1, "Alerta Vermelho": 2}

MEDICAO = "medição"
PREVISAO = "previsão"

# Frases amigáveis por (tipo de gatilho, nível, origem)
ALERT_MESSAGES = {
    ("chuva", "Atenção", MEDICAO): "Chuva forte acontecendo agora",
    ("chuva", "Atenção", PREVISAO): "Chuva forte prevista para as próximas horas",
    ("chuva", "Alerta Vermelho", MEDICAO): "Chuva muito intensa agora — risco de alagamento",
    ("chuva", "Alerta Vermelho", PREVISAO): "Chuva muito intensa prevista — risco de alagamento nas próximas horas",
    ("acumulado", "Atenção", MEDICAO): "Muita chuva acumulada — solo encharcado, atenção a áreas baixas",
    ("acumulado", "Alerta Vermelho", MEDICAO): "Chuva acumulada crítica — risco de enchente em áreas baixas",
    ("vento", "Atenção", MEDICAO): "Ventania — vento forte",
    ("vento", "Alerta Vermelho", MEDICAO): "Vento muito forte — risco de queda de galhos e objetos"
}

KIND_ORDER = {"chuva": 0, "acumulado": 1, "vento": 2}


def _num(value):
    return f"{value:.1f}".replace(".", ",")

def _hour(time):
    # "2026-10-12T18:00" -> "18:00"
    return time.split("T")[-1]

def _trigger(kind, level, origin, technical):
    return {
        "kind": kind,
        "level": level,
        "origin": origin,
        "reason": technical,
        "message": f"{ALERT_MESSAGES[(kind, level, origin)]} ({technical})"
    }

def _rain_now_trigger(rain_now):
    for level in ("Alerta Vermelho", "Atenção"):
        limit = ALERT_THRESHOLDS[level]["rain_now_mm_h"]
        if rain_now >= limit:
            return _trigger("chuva", level, MEDICAO, f"{_num(rain_now)} mm/h medidos agora; limite {limit} mm/h")
    return None

def _forecast_trigger(forecast):
    values = [h.get("precipitation") or 0 for h in forecast]

    limit = ALERT_THRESHOLDS["Alerta Vermelho"]["forecast_3h_mm"]
    for i in range(len(values) - 2):
        total = sum(values[i:i + 3])
        if total >= limit:
            return _trigger("chuva", "Alerta Vermelho", PREVISAO,
                            f"{_num(total)} mm previstos em 3h, até {_hour(forecast[i + 2]['time'])}; limite {limit} mm em 3h")

    limit = ALERT_THRESHOLDS["Atenção"]["forecast_1h_mm"]
    for i, value in enumerate(values):
        if value >= limit:
            return _trigger("chuva", "Atenção", PREVISAO,
                            f"{_num(value)} mm previstos em 1h, até {_hour(forecast[i]['time'])}; limite {limit} mm em 1h")
    return None

def _accumulated_trigger(accumulated_24h):
    for level in ("Alerta Vermelho", "Atenção"):
        limit = ALERT_THRESHOLDS[level]["accumulated_24h_mm"]
        if accumulated_24h >= limit:
            return _trigger("acumulado", level, MEDICAO, f"{_num(accumulated_24h)} mm nas últimas 24h; limite {limit} mm")
    return None

def _wind_trigger(wind_speed):
    for level in ("Alerta Vermelho", "Atenção"):
        limit = ALERT_THRESHOLDS[level]["wind_km_h"]
        if wind_speed >= limit:
            return _trigger("vento", level, MEDICAO, f"{_num(wind_speed)} km/h medidos agora; limite {limit} km/h")
    return None

def evaluate_alert(rain_now, wind_speed, accumulated_24h, forecast):
    """Avalia o nível de alerta de uma cidade.

    rain_now: chuva medida agora (mm/h); wind_speed: vento medido (km/h);
    accumulated_24h: chuva acumulada nas últimas 24h (mm);
    forecast: lista de {"time", "precipitation"} das próximas horas.

    Devolve {"level": ..., "triggers": [...]}. Os gatilhos vêm ordenados do
    mais grave para o menos grave (medição antes de previsão no mesmo nível);
    o primeiro é o motivo principal.
    """
    triggers = [
        _rain_now_trigger(rain_now or 0),
        _forecast_trigger(forecast or []),
        _accumulated_trigger(accumulated_24h or 0),
        _wind_trigger(wind_speed) if wind_speed is not None else None
    ]
    triggers = [t for t in triggers if t is not None]
    triggers.sort(key=lambda t: (-LEVEL_ORDER[t["level"]], t["origin"] != MEDICAO, KIND_ORDER[t["kind"]]))
    level = triggers[0]["level"] if triggers else "Normal"
    return {"level": level, "triggers": triggers}

def accumulated_rain(readings, now, window_hours=24):
    """Soma a chuva (mm) das últimas `window_hours` horas.

    readings: lista de (datetime, taxa em mm/h) em ordem cronológica.
    Cada leitura vale pela sua taxa desde o horário dela até a próxima
    coleta (a última vale até `now`), limitada a MAX_READING_HOURS.
    Só entra a parte de cada intervalo que cai dentro da janela.
    """
    window_start = now - timedelta(hours=window_hours)
    total = 0.0
    for i, (time, rate) in enumerate(readings):
        end = readings[i + 1][0] if i + 1 < len(readings) else now
        end = min(end, time + timedelta(hours=MAX_READING_HOURS), now)
        start = max(time, window_start)
        if end > start:
            total += (rate or 0) * (end - start).total_seconds() / 3600
    return total
