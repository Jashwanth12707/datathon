import random

from .utils import GENDERS, OCCUPATIONS, fake, fir_id, person_name, phone_number, simple_id


FIELDS = [
    "victim_id", "fir_id", "name", "gender", "age", "occupation", "phone",
    "address", "injury_type", "hospital", "statement_recorded",
]


INJURIES = ["None", "Minor", "Grievous", "Fatal", "Emotional Trauma", "Financial Loss"]
HOSPITALS = ["Victoria Hospital", "Bowring Hospital", "KIMS Hubballi", "Wenlock Hospital", "KR Hospital", "District Hospital"]


def rows(count, fir_count):
    for index in range(1, count + 1):
        gender = random.choice(GENDERS)
        injury = random.choices(INJURIES, [42, 28, 8, 2, 8, 12])[0]
        yield {
            "victim_id": simple_id("VIC", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            "name": person_name(gender),
            "gender": gender,
            "age": random.randint(1, 88),
            "occupation": random.choice(OCCUPATIONS),
            "phone": phone_number(),
            "address": fake.address().replace("\n", ", "),
            "injury_type": injury,
            "hospital": random.choice(HOSPITALS) if injury not in ("None", "Financial Loss") else "",
            "statement_recorded": random.choice(["true", "true", "true", "false"]),
        }

