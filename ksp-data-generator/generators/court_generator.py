import random
from datetime import timedelta

from .utils import fake, fir_id, random_date, simple_id


FIELDS = [
    "case_id", "fir_id", "court_name", "judge", "public_prosecutor",
    "charge_sheet_date", "hearing_date", "verdict", "sentence", "case_status",
]


COURTS = [
    "CJM Court Bengaluru", "Sessions Court Bengaluru", "JMFC Mysuru", "JMFC Mangaluru",
    "District and Sessions Court Dharwad", "JMFC Belagavi", "Special NDPS Court Bengaluru",
    "Cyber Crime Court Bengaluru",
]


def rows(count, fir_count):
    for index in range(1, count + 1):
        base_date = random_date()
        status = random.choices(["Pending", "Trial", "Disposed", "Appeal", "Convicted", "Acquitted"], [32, 24, 18, 5, 12, 9])[0]
        verdict = "" if status in ("Pending", "Trial") else random.choice(["Guilty", "Not Guilty", "Compounded", "Dismissed"])
        yield {
            "case_id": simple_id("CASE", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            "court_name": random.choice(COURTS),
            "judge": fake.name(),
            "public_prosecutor": fake.name(),
            "charge_sheet_date": (base_date + timedelta(days=random.randint(30, 120))).isoformat(),
            "hearing_date": (base_date + timedelta(days=random.randint(121, 900))).isoformat(),
            "verdict": verdict,
            "sentence": random.choice(["Fine", "Simple imprisonment", "Rigorous imprisonment", "Probation", ""]) if verdict == "Guilty" else "",
            "case_status": status,
        }

