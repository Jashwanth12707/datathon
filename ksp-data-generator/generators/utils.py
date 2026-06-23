import csv
import calendar
import random
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
from faker import Faker

from config import END_YEAR, FIR_ID_PREFIX, ID_PAD, RANDOM_SEED, START_YEAR


fake = Faker("en_IN")
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


KARNATAKA_LOCATIONS = [
    {"district": "Bengaluru Urban", "taluk": "Bengaluru North", "place": "Yelahanka", "lat": 13.1007, "lon": 77.5963, "urban": True},
    {"district": "Bengaluru Urban", "taluk": "Bengaluru South", "place": "Jayanagar", "lat": 12.9250, "lon": 77.5938, "urban": True},
    {"district": "Bengaluru Urban", "taluk": "Anekal", "place": "Electronic City", "lat": 12.8452, "lon": 77.6602, "urban": True},
    {"district": "Bengaluru Rural", "taluk": "Devanahalli", "place": "Devanahalli", "lat": 13.2466, "lon": 77.7137, "urban": False},
    {"district": "Mysuru", "taluk": "Mysuru", "place": "Lakshmipuram", "lat": 12.2958, "lon": 76.6394, "urban": True},
    {"district": "Mysuru", "taluk": "Nanjangud", "place": "Nanjangud", "lat": 12.1200, "lon": 76.6800, "urban": False},
    {"district": "Mangaluru", "taluk": "Mangaluru", "place": "Kadri", "lat": 12.8944, "lon": 74.8560, "urban": True},
    {"district": "Udupi", "taluk": "Udupi", "place": "Manipal", "lat": 13.3525, "lon": 74.7864, "urban": True},
    {"district": "Dharwad", "taluk": "Hubballi", "place": "Vidyanagar", "lat": 15.3647, "lon": 75.1239, "urban": True},
    {"district": "Belagavi", "taluk": "Belagavi", "place": "Tilakwadi", "lat": 15.8497, "lon": 74.4977, "urban": True},
    {"district": "Ballari", "taluk": "Ballari", "place": "Cowl Bazaar", "lat": 15.1394, "lon": 76.9214, "urban": True},
    {"district": "Vijayapura", "taluk": "Vijayapura", "place": "Gol Gumbaz Road", "lat": 16.8302, "lon": 75.7100, "urban": True},
    {"district": "Kalaburagi", "taluk": "Kalaburagi", "place": "Station Bazar", "lat": 17.3297, "lon": 76.8343, "urban": True},
    {"district": "Bidar", "taluk": "Bidar", "place": "Naubad", "lat": 17.9133, "lon": 77.5301, "urban": True},
    {"district": "Raichur", "taluk": "Raichur", "place": "Manvi", "lat": 15.9913, "lon": 77.0500, "urban": False},
    {"district": "Koppal", "taluk": "Gangavathi", "place": "Gangavathi", "lat": 15.4319, "lon": 76.5293, "urban": False},
    {"district": "Hassan", "taluk": "Hassan", "place": "Hassan Town", "lat": 13.0033, "lon": 76.1004, "urban": True},
    {"district": "Shivamogga", "taluk": "Shivamogga", "place": "Sagar Road", "lat": 13.9299, "lon": 75.5681, "urban": True},
    {"district": "Tumakuru", "taluk": "Tumakuru", "place": "Sira Gate", "lat": 13.3409, "lon": 77.1010, "urban": True},
    {"district": "Mandya", "taluk": "Mandya", "place": "Maddur", "lat": 12.5849, "lon": 77.0464, "urban": False},
    {"district": "Chikkamagaluru", "taluk": "Chikkamagaluru", "place": "Kadur", "lat": 13.5528, "lon": 76.0111, "urban": False},
    {"district": "Kodagu", "taluk": "Madikeri", "place": "Madikeri", "lat": 12.4244, "lon": 75.7382, "urban": False},
    {"district": "Chitradurga", "taluk": "Chitradurga", "place": "Hiriyur", "lat": 13.9446, "lon": 76.6167, "urban": False},
    {"district": "Kolar", "taluk": "Kolar", "place": "Bangarpet", "lat": 12.9920, "lon": 78.1780, "urban": False},
    {"district": "Dakshina Kannada", "taluk": "Puttur", "place": "Puttur", "lat": 12.7648, "lon": 75.1842, "urban": False},
]


CRIME_PROFILES = {
    "Vehicle Theft": {"acts": ["IPC"], "sections": ["379"], "hours": [(21, 23), (0, 5)], "weight": 13},
    "Cyber Fraud": {"acts": ["IT Act", "IPC"], "sections": ["66C", "66D", "420"], "hours": [(10, 17)], "weight": 16},
    "Chain Snatching": {"acts": ["IPC"], "sections": ["356", "379"], "hours": [(6, 9), (18, 21)], "weight": 8},
    "Domestic Violence": {"acts": ["IPC", "DV Act"], "sections": ["498A", "323", "506"], "hours": [(20, 23), (0, 2)], "weight": 9},
    "Road Accident": {"acts": ["IPC", "MV Act"], "sections": ["279", "337", "338"], "hours": [(8, 11), (17, 22)], "weight": 18},
    "Burglary": {"acts": ["IPC"], "sections": ["454", "457", "380"], "hours": [(22, 23), (0, 4)], "weight": 10},
    "Assault": {"acts": ["IPC"], "sections": ["323", "324", "504", "506"], "hours": [(18, 23)], "weight": 12},
    "Narcotics": {"acts": ["NDPS Act"], "sections": ["20(b)", "21", "22"], "hours": [(19, 23), (0, 3)], "weight": 5},
    "Election Violence": {"acts": ["IPC", "RP Act"], "sections": ["147", "148", "171F"], "hours": [(10, 22)], "weight": 3},
    "Festival Crowd Crime": {"acts": ["IPC"], "sections": ["379", "356", "323"], "hours": [(17, 23)], "weight": 6},
}


OCCUPATIONS = [
    "Student", "Software Engineer", "Auto Driver", "Shop Owner", "Farmer", "Teacher",
    "Homemaker", "Security Guard", "Bank Employee", "Daily Wage Worker", "Retired",
    "Police Constable", "Delivery Partner", "Nurse", "Business Owner",
]

STATUSES = ["Under Investigation", "Charge Sheet Filed", "Closed", "Pending Trial", "Convicted", "Acquitted"]
GENDERS = ["Male", "Female", "Other"]


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def fir_id(index):
    return f"{FIR_ID_PREFIX}-{str(index).zfill(ID_PAD)}"


def simple_id(prefix, index):
    return f"{prefix}-{str(index).zfill(ID_PAD)}"


def weighted_choice(items):
    labels = list(items.keys())
    weights = [items[label]["weight"] for label in labels]
    return random.choices(labels, weights=weights, k=1)[0]


def random_date():
    start = date(START_YEAR, 1, 1)
    end = date(END_YEAR, 12, 31)
    total_days = (end - start).days
    selected = start + timedelta(days=random.randint(0, total_days))
    if selected.month in (8, 9, 10, 11) and random.random() < 0.12:
        festival_month = random.choice([8, 9, 10, 11])
        max_day = calendar.monthrange(selected.year, festival_month)[1]
        selected = selected.replace(month=festival_month, day=min(selected.day, max_day))
    return selected


def crime_for_date(selected_date):
    if selected_date.month in (4, 5) and random.random() < 0.25:
        return "Election Violence"
    if selected_date.month in (9, 10, 11) and random.random() < 0.28:
        return "Festival Crowd Crime"
    if selected_date.month in (6, 7, 8, 9) and random.random() < 0.18:
        return "Road Accident"
    return weighted_choice(CRIME_PROFILES)


def random_time_for_crime(crime_type):
    ranges = CRIME_PROFILES[crime_type]["hours"]
    start_hour, end_hour = random.choice(ranges)
    if start_hour <= end_hour:
        hour = random.randint(start_hour, end_hour)
    else:
        hour = random.choice(list(range(start_hour, 24)) + list(range(0, end_hour + 1)))
    return time(hour, random.randint(0, 59), random.randint(0, 59))


def jitter_coordinate(value, scale=0.035):
    return round(value + float(np.random.normal(0, scale)), 6)


def choose_location():
    return random.choice(KARNATAKA_LOCATIONS)


def station_name(location, ordinal=None):
    suffixes = ["Town", "Rural", "Traffic", "Women", "Market", "East", "West", "North", "South"]
    suffix = suffixes[(ordinal or random.randint(0, len(suffixes) - 1)) % len(suffixes)]
    return f"{location['place']} {suffix} Police Station"


def person_name(gender=None):
    if gender == "Female":
        return fake.name_female()
    if gender == "Male":
        return fake.name_male()
    return fake.name()


def phone_number():
    return f"9{random.randint(100000000, 999999999)}"


def aadhaar_last4():
    return str(random.randint(0, 9999)).zfill(4)


def vehicle_registration():
    districts = ["KA01", "KA02", "KA03", "KA04", "KA05", "KA09", "KA19", "KA22", "KA25", "KA32", "KA51", "KA53"]
    return f"{random.choice(districts)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000, 9999)}"


def uuid_text():
    return str(uuid.uuid4())


@contextmanager
def csv_writer(path, fieldnames):
    ensure_dir(Path(path).parent)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        yield writer


def write_rows(path, fieldnames, rows, total=None, description=None):
    from tqdm import tqdm

    with csv_writer(path, fieldnames) as writer:
        iterator = tqdm(rows, total=total, desc=description, unit="row")
        for row in iterator:
            writer.writerow(row)


def created_at_for(day):
    dt = datetime.combine(day, time(random.randint(8, 22), random.randint(0, 59), random.randint(0, 59)))
    return dt.isoformat(sep=" ")
