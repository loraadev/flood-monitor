CITIES = [
    {"slug": "adamantina", "name": "Adamantina", "latitude": -21.68528, "longitude": -51.0725},
    {"slug": "lucelia", "name": "Lucélia", "latitude": -21.72028, "longitude": -51.01889},
    {"slug": "osvaldo-cruz", "name": "Osvaldo Cruz", "latitude": -21.79667, "longitude": -50.87861},
    {"slug": "inubia-paulista", "name": "Inúbia Paulista", "latitude": -21.76972, "longitude": -50.96194}
]

DEFAULT_CITY_SLUG = "osvaldo-cruz"

def get_city(slug):
    for city in CITIES:
        if city["slug"] == slug:
            return city
    return None
