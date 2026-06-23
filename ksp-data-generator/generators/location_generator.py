import random

from .utils import KARNATAKA_LOCATIONS, jitter_coordinate, simple_id, station_name


FIELDS = [
    "location_id", "district", "taluk", "village_or_ward", "police_station",
    "latitude", "longitude", "jurisdiction_type",
]


def rows(count):
    for index in range(1, count + 1):
        base = KARNATAKA_LOCATIONS[(index - 1) % len(KARNATAKA_LOCATIONS)]
        ward = f"Ward {random.randint(1, 198)}" if base["urban"] else f"{base['place']} Village"
        yield {
            "location_id": simple_id("LOC", index),
            "district": base["district"],
            "taluk": base["taluk"],
            "village_or_ward": ward,
            "police_station": station_name(base, index),
            "latitude": jitter_coordinate(base["lat"], 0.02),
            "longitude": jitter_coordinate(base["lon"], 0.02),
            "jurisdiction_type": "Urban" if base["urban"] else "Rural",
        }

