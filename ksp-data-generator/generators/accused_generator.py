import random

from .gang_generator import gang_id_for
from .utils import GENDERS, OCCUPATIONS, aadhaar_last4, fake, fir_id, person_name, phone_number, simple_id


FIELDS = [
    "accused_id", "fir_id", "name", "gender", "age", "occupation", "address",
    "mobile", "aadhaar_last4", "known_alias", "gang_id", "history_sheeter",
    "wanted", "status",
]


ALIASES = ["Appu", "Kariya", "Tiger", "Macha", "Ravi Boss", "Silent", "Munna", "Rocky", ""]
STATUSES = ["Arrested", "Absconding", "On Bail", "Notice Issued", "Remanded", "Unknown"]


def rows(count, fir_count, gang_count):
    repeat_profiles = []
    pool_size = max(100, min(50000, count // 3 or 100))
    for _ in range(pool_size):
        gender = random.choice(GENDERS[:2])
        repeat_profiles.append({
            "name": person_name(gender),
            "gender": gender,
            "age": random.randint(18, 62),
            "occupation": random.choice(OCCUPATIONS),
            "address": fake.address().replace("\n", ", "),
            "mobile": phone_number(),
            "aadhaar_last4": aadhaar_last4(),
            "known_alias": random.choice(ALIASES),
            "gang_id": gang_id_for(_, gang_count),
        })

    for index in range(1, count + 1):
        profile = random.choice(repeat_profiles) if random.random() < 0.45 else None
        if profile is None:
            gender = random.choice(GENDERS)
            profile = {
                "name": person_name(gender),
                "gender": gender,
                "age": random.randint(16, 75),
                "occupation": random.choice(OCCUPATIONS),
                "address": fake.address().replace("\n", ", "),
                "mobile": phone_number(),
                "aadhaar_last4": aadhaar_last4(),
                "known_alias": random.choice(ALIASES),
                "gang_id": gang_id_for(index, gang_count),
            }
        history_sheeter = "true" if profile["gang_id"] or random.random() < 0.16 else "false"
        yield {
            "accused_id": simple_id("ACC", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            **profile,
            "history_sheeter": history_sheeter,
            "wanted": "true" if random.random() < 0.08 else "false",
            "status": random.choices(STATUSES, [38, 14, 20, 12, 10, 6])[0],
        }

