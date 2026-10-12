from datetime import datetime, timedelta
from analyzer import evaluate_alert, accumulated_rain, LEVEL_ORDER
from database import create_table, get_alert_level, set_alert_level, reset_alert_levels
from telegram_bot import notify_city

def check_alert(city, rain_now, wind_speed, accumulated_24h, forecast, now, notify=True):
    """Avalia o risco da cidade e decide se alerta.

    Só alerta quando o nível SOBE em relação ao último notificado
    (Normal -> Atenção -> Alerta Vermelho). No mesmo nível não repete.
    Quando o nível baixa, o estado é atualizado sem alertar, para que uma
    nova subida volte a disparar. Com notify=True, envia o alerta pelo
    Telegram aos inscritos da cidade.
    """
    result = evaluate_alert(rain_now, wind_speed, accumulated_24h, forecast)
    level = result["level"]
    previous = get_alert_level(city)
    stamp = now.strftime("%d/%m/%Y %H:%M")

    if LEVEL_ORDER[level] > LEVEL_ORDER[previous]:
        main = result["triggers"][0]
        print(f"ALERTARIA: {city}, {level}, {main['origin']}, {main['message']}")
        for other in result["triggers"][1:]:
            print(f"    também: {other['level']}, {other['origin']}, {other['message']}")
        set_alert_level(city, level, stamp)
        result["status"] = "alertaria"
        if notify:
            # Falha no envio não desfaz o registro do novo nível
            try:
                notify_city(city, level, main["message"])
            except Exception as e:
                print(f"Erro ao enviar alerta de {city} pelo Telegram: {type(e).__name__}")
    elif LEVEL_ORDER[level] < LEVEL_ORDER[previous]:
        print(f"[alerta] {city}: nível baixou de {previous} para {level} (sem alerta)")
        set_alert_level(city, level, stamp)
        result["status"] = "baixou"
    else:
        result["status"] = "mantido"
    return result


# ---------------------------------------------------------------------
# Simulação — usa só cidades fictícias; não toca no estado das reais.
# Rode com: python alerts.py
# ---------------------------------------------------------------------
TEST_CITIES = ["Teste Chuva", "Teste Vento", "Teste Previsão", "Teste Acumulado"]

def _forecast(now, values):
    # Monta uma previsão horária a partir de uma lista de mm por hora
    start = now.replace(minute=0, second=0, microsecond=0)
    return [{"time": (start + timedelta(hours=i + 1)).strftime("%Y-%m-%dT%H:%M"), "precipitation": v}
            for i, v in enumerate(values)]

def simulate():
    create_table()
    reset_alert_levels(TEST_CITIES)
    now = datetime(2026, 1, 15, 14, 0)
    dry = _forecast(now, [0] * 12)

    def step(title, city, rain=0, wind=10, accumulated=0, forecast=dry):
        print(f"\n> {title}")
        # notify=False: a simulação nunca envia mensagens de verdade
        result = check_alert(city, rain, wind, accumulated, forecast, now, notify=False)
        if result["status"] == "mantido":
            print(f"  (sem novo alerta: {city} continua em {result['level']})")

    print("=== Chuva medida ===")
    step("Chuva fraca, 5 mm/h", "Teste Chuva", rain=5)
    step("Chuva forte, 30 mm/h", "Teste Chuva", rain=30)
    step("Repetição no mesmo nível, 35 mm/h", "Teste Chuva", rain=35)
    step("Piora para 60 mm/h", "Teste Chuva", rain=60)
    step("Repetição no Alerta Vermelho, 55 mm/h", "Teste Chuva", rain=55)
    step("Queda para 10 mm/h", "Teste Chuva", rain=10)
    step("Resubida para 28 mm/h", "Teste Chuva", rain=28)

    print("\n=== Vento ===")
    step("Vento de 55 km/h", "Teste Vento", wind=55)
    step("Vento de 95 km/h", "Teste Vento", wind=95)

    print("\n=== Previsão ===")
    step("Previsão de 30 mm numa hora", "Teste Previsão", forecast=_forecast(now, [0, 2, 30, 4] + [0] * 8))
    step("Previsão de 20 + 18 + 15 mm em 3 horas seguidas", "Teste Previsão", forecast=_forecast(now, [0, 20, 18, 15] + [0] * 8))

    print("\n=== Acúmulo de 24h ===")
    # 48 coletas de 30 em 30 min com 2,2 mm/h: nenhuma sozinha alertaria
    readings = [(now - timedelta(minutes=30 * i), 2.2) for i in range(48, 0, -1)]
    total = accumulated_rain(readings, now)
    print(f"  acúmulo calculado: {total:.1f} mm (2,2 mm/h durante 24h)")
    step("Garoa contínua por 24h", "Teste Acumulado", rain=2.2, accumulated=total)
    # Leitura de 10 mm/h seguida de 6h sem coletas: conta no máximo 1h
    gap = [(now - timedelta(hours=7), 10), (now - timedelta(hours=1), 0)]
    print(f"  com servidor parado 6h após leitura de 10 mm/h: {accumulated_rain(gap, now):.1f} mm (não 60 mm)")

    print("\n=== Estado final ===")
    for city in TEST_CITIES:
        print(f"  {city}: {get_alert_level(city)}")

if __name__ == "__main__":
    simulate()
