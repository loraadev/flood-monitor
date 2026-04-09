def analyze_risk(rain_1h):
    if rain_1h is None:
        rain_1h = 0

    if rain_1h < 5:
        return "Normal"
    elif rain_1h < 25:
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