import random

from .utils import KARNATAKA_LOCATIONS, fake, jitter_coordinate, phone_number, simple_id, station_name


FIELDS = [
    "station_id", "district", "police_station", "station_type", "address",
    "latitude", "longitude", "phone", "email", "circle", "subdivision",
]


def rows(count):
    for index in range(1, count + 1):
        base = KARNATAKA_LOCATIONS[(index - 1) % len(KARNATAKA_LOCATIONS)]
        name = station_name(base, index)
        slug = name.lower().replace(" ", ".")
        yield {
            "station_id": simple_id("PS", index),
            "district": base["district"],
            "police_station": name,
            "station_type": random.choice(["Law and Order", "Traffic", "Women", "Cyber Crime", "Rural"]),
            "address": fake.address().replace("\n", ", "),
            "latitude": jitter_coordinate(base["lat"], 0.015),
            "longitude": jitter_coordinate(base["lon"], 0.015),
            "phone": phone_number(),
            "email": f"{slug}@ksp.gov.in",
            "circle": f"{base['place']} Circle",
            "subdivision": f"{base['taluk']} Subdivision",
        }

