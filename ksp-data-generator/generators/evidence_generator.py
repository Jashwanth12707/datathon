import random
from datetime import timedelta

from .utils import fir_id, random_date, simple_id


FIELDS = [
    "evidence_id", "fir_id", "type", "description", "forensic_lab",
    "collected_by", "collection_date", "status",
]


TYPES = ["CCTV footage", "Mobile phone", "Fingerprint", "Blood sample", "Vehicle part", "Document", "Bank statement", "Weapon", "Clothing"]
LABS = ["RFSL Bengaluru", "FSL Madiwala", "RFSL Mysuru", "RFSL Dharwad", "Cyber Forensic Lab CID", ""]


def rows(count, fir_count, officer_count):
    for index in range(1, count + 1):
        evidence_type = random.choice(TYPES)
        yield {
            "evidence_id": simple_id("EVD", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            "type": evidence_type,
            "description": f"{evidence_type} collected and sealed under panchanama",
            "forensic_lab": random.choice(LABS),
            "collected_by": simple_id("OFF", random.randint(1, max(1, officer_count))),
            "collection_date": (random_date() + timedelta(days=random.randint(0, 14))).isoformat(),
            "status": random.choice(["Collected", "Sent to Lab", "Report Received", "Returned", "Disposed"]),
        }

