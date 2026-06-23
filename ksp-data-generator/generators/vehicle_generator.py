import random

from .utils import fake, fir_id, simple_id, vehicle_registration


FIELDS = [
    "vehicle_id", "owner", "registration_number", "engine_number", "chassis_number",
    "vehicle_type", "color", "manufacturer", "status", "linked_fir",
]


TYPES = ["Motorcycle", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Tractor", "Tempo"]
COLORS = ["White", "Black", "Silver", "Red", "Blue", "Grey", "Green", "Yellow"]
MAKERS = ["Hero", "Honda", "TVS", "Bajaj", "Maruti Suzuki", "Hyundai", "Tata", "Mahindra", "Toyota", "Ashok Leyland"]


def rows(count, fir_count):
    for index in range(1, count + 1):
        linked = random.random() < 0.72
        yield {
            "vehicle_id": simple_id("VEH", index),
            "owner": fake.name(),
            "registration_number": vehicle_registration(),
            "engine_number": f"EN{random.randint(10000000, 99999999)}",
            "chassis_number": f"CH{random.randint(100000000000, 999999999999)}",
            "vehicle_type": random.choice(TYPES),
            "color": random.choice(COLORS),
            "manufacturer": random.choice(MAKERS),
            "status": random.choice(["Stolen", "Recovered", "Seized", "Released", "Involved", "Unknown"]),
            "linked_fir": fir_id(random.randint(1, fir_count)) if linked else "",
        }

