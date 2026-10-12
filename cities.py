CITIES = [
    {"slug": "adamantina", "name": "Adamantina", "latitude": -21.68528, "longitude": -51.0725},
    {"slug": "lucelia", "name": "Lucélia", "latitude": -21.72028, "longitude": -51.01889},
    {"slug": "osvaldo-cruz", "name": "Osvaldo Cruz", "latitude": -21.79667, "longitude": -50.87861},
    {"slug": "bauru", "name": "Bauru", "latitude": -22.31472, "longitude": -49.06056},
    {"slug": "sao-carlos", "name": "São Carlos", "latitude": -22.0175, "longitude": -47.89083},
    {"slug": "ribeirao-preto", "name": "Ribeirão Preto", "latitude": -21.1775, "longitude": -47.81028},
    {"slug": "piracicaba", "name": "Piracicaba", "latitude": -22.72528, "longitude": -47.64917},
    {"slug": "bora", "name": "Borá", "latitude": -22.26972, "longitude": -50.53444}
]

DEFAULT_CITY_SLUG = "osvaldo-cruz"

def get_city(slug):
    for city in CITIES:
        if city["slug"] == slug:
            return city
    return None
