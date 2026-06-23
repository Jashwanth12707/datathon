import random

from .utils import KARNATAKA_LOCATIONS, fir_id, jitter_coordinate, simple_id


FIELDS = [
    "camera_id", "owner", "location", "latitude", "longitude", "coverage_angle",
    "resolution", "status", "linked_fir",
]


OWNERS = ["BBMP", "Smart City Mission", "Private Shop", "Apartment Association", "Traffic Police", "Bank", "Petrol Pump"]


def rows(count, fir_count):
    for index in range(1, count + 1):
        loc = random.choice(KARNATAKA_LOCATIONS)
        yield {
            "camera_id": simple_id("CAM", index),
            "owner": random.choice(OWNERS),
            "location": f"{loc['place']} {random.choice(['Junction', 'Main Road', 'Market', 'Bus Stand', 'Toll Gate'])}",
            "latitude": jitter_coordinate(loc["lat"], 0.025),
            "longitude": jitter_coordinate(loc["lon"], 0.025),
            "coverage_angle": random.choice([60, 90, 120, 180, 270, 360]),
            "resolution": random.choice(["720p", "1080p", "2K", "4K"]),
            "status": random.choice(["Active", "Inactive", "Maintenance", "Footage Retrieved"]),
            "linked_fir": fir_id(random.randint(1, fir_count)) if random.random() < 0.35 else "",
        }

