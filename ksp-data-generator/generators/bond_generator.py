import random
from datetime import timedelta

from .utils import fake, fir_id, random_date, simple_id


FIELDS = [
    "bond_id", "fir_id", "accused_id", "bond_type", "surety_name", "bond_amount",
    "execution_date", "expiry_date", "status",
]


def rows(count, fir_count, accused_count):
    for index in range(1, count + 1):
        execution = random_date() + timedelta(days=random.randint(7, 180))
        yield {
            "bond_id": simple_id("BOND", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            "accused_id": simple_id("ACC", random.randint(1, max(1, accused_count))),
            "bond_type": random.choice(["Personal Bond", "Surety Bond", "Bailable Warrant Bond", "Good Behaviour Bond"]),
            "surety_name": fake.name(),
            "bond_amount": random.choice([5000, 10000, 25000, 50000, 100000, 200000]),
            "execution_date": execution.isoformat(),
            "expiry_date": (execution + timedelta(days=random.choice([90, 180, 365, 730]))).isoformat(),
            "status": random.choice(["Active", "Forfeited", "Closed", "Extended"]),
        }

