import random

from .utils import GENDERS, KARNATAKA_LOCATIONS, fake, person_name, phone_number, simple_id, station_name


FIELDS = [
    "officer_id", "name", "gender", "rank", "badge_no", "district",
    "police_station", "phone", "email", "active",
]


RANKS = ["Police Constable", "Head Constable", "ASI", "PSI", "PI", "DySP", "ACP", "SP"]


def rows(count):
    for index in range(1, count + 1):
        gender = random.choice(GENDERS[:2])
        loc = random.choice(KARNATAKA_LOCATIONS)
        name = person_name(gender)
        yield {
            "officer_id": simple_id("OFF", index),
            "name": name,
            "gender": gender,
            "rank": random.choices(RANKS, [35, 20, 13, 14, 10, 4, 2, 2])[0],
            "badge_no": f"KSP{random.randint(10000, 99999)}",
            "district": loc["district"],
            "police_station": station_name(loc, index),
            "phone": phone_number(),
            "email": f"{name.lower().replace(' ', '.')}.{index}@ksp.gov.in",
            "active": random.choice(["true", "true", "true", "false"]),
        }

