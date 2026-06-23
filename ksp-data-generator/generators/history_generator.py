import random

from .utils import KARNATAKA_LOCATIONS, fir_id, simple_id


FIELDS = [
    "history_sheet_id", "accused_id", "name", "police_station", "district",
    "category", "opened_on", "last_reviewed", "fir_count", "risk_score",
    "remarks",
]


def rows(count, accused_count):
    for index in range(1, count + 1):
        loc = random.choice(KARNATAKA_LOCATIONS)
        risk = random.randint(35, 100)
        accused_index = random.randint(1, max(1, accused_count))
        yield {
            "history_sheet_id": simple_id("HS", index),
            "accused_id": simple_id("ACC", accused_index),
            "name": f"Linked Accused {accused_index}",
            "police_station": f"{loc['place']} Town Police Station",
            "district": loc["district"],
            "category": random.choice(["Rowdy Sheet", "MOB", "Habitual Offender", "Cyber Repeat Offender", "NDPS Watch"]),
            "opened_on": f"{random.randint(2000, 2025)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "last_reviewed": f"2026-{random.randint(1, 6):02d}-{random.randint(1, 28):02d}",
            "fir_count": random.randint(2, 38),
            "risk_score": risk,
            "remarks": f"Linked to FIR {fir_id(random.randint(1, max(1, accused_count)))} and local associate network",
        }

