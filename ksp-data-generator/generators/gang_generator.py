import random

from .utils import KARNATAKA_LOCATIONS, fake, simple_id


FIELDS = [
    "gang_id", "gang_name", "base_district", "base_area", "primary_activity",
    "member_count_estimate", "active_since", "risk_level",
]


ACTIVITIES = ["Vehicle theft", "Extortion", "Cyber fraud", "Narcotics", "Chain snatching", "Burglary"]


def rows(count):
    for index in range(1, count + 1):
        loc = random.choice(KARNATAKA_LOCATIONS)
        yield {
            "gang_id": simple_id("GANG", index),
            "gang_name": f"{loc['place']} {random.choice(['Boys', 'Crew', 'Circle', 'Group', 'Syndicate'])}",
            "base_district": loc["district"],
            "base_area": loc["place"],
            "primary_activity": random.choice(ACTIVITIES),
            "member_count_estimate": random.randint(3, 80),
            "active_since": random.randint(1995, 2025),
            "risk_level": random.choice(["Low", "Medium", "High", "Severe"]),
        }


def gang_id_for(index, gang_count):
    if gang_count <= 0 or random.random() > 0.38:
        return ""
    return simple_id("GANG", random.randint(1, gang_count))

