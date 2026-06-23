import random
from datetime import timedelta

from .utils import GENDERS, OCCUPATIONS, fake, fir_id, person_name, random_date, simple_id


FIELDS = ["witness_id", "fir_id", "name", "age", "gender", "occupation", "statement_date"]


def rows(count, fir_count):
    for index in range(1, count + 1):
        gender = random.choice(GENDERS)
        yield {
            "witness_id": simple_id("WIT", index),
            "fir_id": fir_id(random.randint(1, fir_count)),
            "name": person_name(gender),
            "age": random.randint(16, 85),
            "gender": gender,
            "occupation": random.choice(OCCUPATIONS),
            "statement_date": (random_date() + timedelta(days=random.randint(0, 20))).isoformat(),
        }

