import random
from datetime import datetime, timedelta

from .utils import (
    CRIME_PROFILES,
    OCCUPATIONS,
    STATUSES,
    choose_location,
    created_at_for,
    fake,
    fir_id,
    jitter_coordinate,
    person_name,
    random_date,
    random_time_for_crime,
    crime_for_date,
    station_name,
)


FIELDS = [
    "fir_id", "year", "date", "time", "district", "police_station", "beat_no",
    "crime_type", "act", "sections", "occurrence_date", "occurrence_time",
    "occurrence_place", "latitude", "longitude", "complainant_name",
    "complainant_address", "complainant_occupation", "type_of_information",
    "property_stolen", "estimated_loss", "status", "created_at",
]


PROPERTY_BY_CRIME = {
    "Vehicle Theft": ["Two wheeler", "Car", "Auto rickshaw", "Goods vehicle"],
    "Cyber Fraud": ["Bank balance", "UPI wallet balance", "Credit card limit"],
    "Chain Snatching": ["Gold chain", "Mangalsutra", "Mobile phone"],
    "Burglary": ["Gold ornaments", "Cash", "Laptop", "Silver articles"],
    "Festival Crowd Crime": ["Mobile phone", "Wallet", "Gold chain"],
}


def build_fir_row(index):
    reported_date = random_date()
    crime_type = crime_for_date(reported_date)
    occurrence_date = reported_date - timedelta(days=random.choices([0, 1, 2, 3, 7], [70, 18, 6, 4, 2])[0])
    occurrence_time = random_time_for_crime(crime_type)
    location = choose_location()
    profile = CRIME_PROFILES[crime_type]
    property_stolen = random.choice(PROPERTY_BY_CRIME.get(crime_type, ["NA"]))
    estimated_loss = 0 if property_stolen == "NA" else random.randint(500, 750000)
    if crime_type == "Cyber Fraud":
        estimated_loss = random.randint(2000, 2500000)
    if crime_type == "Domestic Violence":
        estimated_loss = 0

    return {
        "fir_id": fir_id(index),
        "year": reported_date.year,
        "date": reported_date.isoformat(),
        "time": datetime.now().replace(
            hour=random.randint(8, 23), minute=random.randint(0, 59), second=random.randint(0, 59)
        ).time().isoformat(timespec="seconds"),
        "district": location["district"],
        "police_station": station_name(location, index),
        "beat_no": f"B-{random.randint(1, 48):02d}",
        "crime_type": crime_type,
        "act": ", ".join(profile["acts"]),
        "sections": ", ".join(profile["sections"]),
        "occurrence_date": occurrence_date.isoformat(),
        "occurrence_time": occurrence_time.isoformat(timespec="seconds"),
        "occurrence_place": f"{location['place']} {random.choice(['Bus Stand', 'Main Road', 'Market', 'Ward', 'Layout', 'Cross'])}",
        "latitude": jitter_coordinate(location["lat"]),
        "longitude": jitter_coordinate(location["lon"]),
        "complainant_name": person_name(),
        "complainant_address": fake.address().replace("\n", ", "),
        "complainant_occupation": random.choice(OCCUPATIONS),
        "type_of_information": random.choice(["Written", "Oral", "Online", "PCR Call", "Zero FIR Transfer"]),
        "property_stolen": property_stolen,
        "estimated_loss": estimated_loss,
        "status": random.choices(STATUSES, [45, 22, 12, 13, 5, 3])[0],
        "created_at": created_at_for(reported_date),
    }


def rows(count):
    for index in range(1, count + 1):
        yield build_fir_row(index)

