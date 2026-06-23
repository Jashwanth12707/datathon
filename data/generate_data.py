import csv
import random
import uuid
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('en_IN')

# ── Karnataka districts and stations ──────────────────────────
DISTRICTS = [
    "Bangalore Urban", "Bangalore Rural", "Mysuru", "Mangaluru",
    "Belagavi", "Kalaburagi", "Davanagere", "Ballari",
    "Shivamogga", "Tumakuru"
]

STATIONS = {
    "Bangalore Urban": ["Koramangala", "Indiranagar", "Whitefield", "Jayanagar", "Hebbal"],
    "Bangalore Rural": ["Anekal", "Devanahalli", "Doddaballapur"],
    "Mysuru": ["Nazarbad", "Vidyaranyapuram", "Lashkar"],
    "Mangaluru": ["Pandeshwar", "Mangaluru North", "Mangaluru South"],
    "Belagavi": ["Belagavi Rural", "Belagavi City", "Gokak"],
    "Kalaburagi": ["Kalaburagi Rural", "Kalaburagi City"],
    "Davanagere": ["Davanagere North", "Davanagere South"],
    "Ballari": ["Ballari Rural", "Ballari City"],
    "Shivamogga": ["Shivamogga Rural", "Shivamogga City"],
    "Tumakuru": ["Tumakuru Rural", "Tumakuru City"]
}


IPC_ACTS = ["IPC", "NDPS Act", "IT Act", "Arms Act", "POCSO Act"]
IPC_SECTIONS = {
    "Theft": "379",
    "Robbery": "392",
    "Assault": "323",
    "Murder": "302",
    "Fraud": "420",
    "Cybercrime": "66C",
    "Kidnapping": "363",
    "Drug Trafficking": "20 NDPS",
    "Domestic Violence": "498A",
    "POCSO": "4 POCSO"
}

CRIME_TYPES = [
    "Theft", "Robbery", "Assault", "Murder", "Fraud",
    "Cybercrime", "Kidnapping", "Drug Trafficking",
    "Domestic Violence", "POCSO"
]

MO_LIST = [
    "Night operation", "Impersonation", "Pick pocketing",
    "Vehicle theft", "Online fraud", "Chain snatching",
    "Housebreaking", "ATM skimming", "Physical assault"
]

STATUS_LIST = ["Open", "Under Investigation", "Closed", "Chargesheeted"]
BOND_STATUS = ["Active", "Expired", "Renewed"]
COURT_STATUS = ["Pending", "Hearing", "Judgement", "Closed"]
GENDER = ["Male", "Female"]

# Karnataka lat/lng bounding box
LAT_MIN, LAT_MAX = 11.5, 18.5
LNG_MIN, LNG_MAX = 74.0, 78.5

def random_lat():
    return round(random.uniform(LAT_MIN, LAT_MAX), 6)

def random_lng():
    return round(random.uniform(LNG_MIN, LNG_MAX), 6)

def random_date(start_year=2020, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")

def random_time():
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    return f"{h:02d}:{m:02d}"


def generate_firs(n=2000):
    firs = []
    for _ in range(n):
        district = random.choice(DISTRICTS)
        station = random.choice(STATIONS[district])
        crime = random.choice(CRIME_TYPES)
        firs.append({
            "fir_id": f"FIR-{uuid.uuid4().hex[:8].upper()}",
            "year": str(random.randint(2020, 2025)),
            "date": random_date(),
            "time": random_time(),
            "district": district,
            "station": station,
            "act": random.choice(IPC_ACTS),
            "sections": IPC_SECTIONS.get(crime, "420"),
            "occurrence_date": random_date(),
            "occurrence_time": random_time(),
            "occurrence_place": fake.address(),
            "beat_no": f"B-{random.randint(1, 50)}",
            "crime_type": crime,
            "complainant_name": fake.name(),
            "complainant_address": fake.address(),
            "complainant_occupation": fake.job(),
            "type_of_info": random.choice(["Written", "Oral"]),
            "property_stolen": random.choice([
                "Gold chain", "Mobile phone", "Cash", "Vehicle", "None", "Laptop"
            ]),
            "status": random.choice(STATUS_LIST),
            "latitude": random_lat(),
            "longitude": random_lng()
        })
    return firs

# ── Generate Accused ──────────────────────────────────────────
def generate_accused(firs, n=1000):
    accused_list = []
    fir_ids = [f["fir_id"] for f in firs]
    for _ in range(n):
        accused_list.append({
            "accused_id": f"ACC-{uuid.uuid4().hex[:8].upper()}",
            "fir_id": random.choice(fir_ids),
            "name": fake.name(),
            "age": random.randint(18, 65),
            "gender": random.choice(GENDER),
            "district": random.choice(DISTRICTS),
            "modus_operandi": random.choice(MO_LIST),
            "risk_score": random.randint(10, 100)
        })
    return accused_list

# ── Generate Victims ──────────────────────────────────────────
def generate_victims(firs, n=1000):
    victims = []
    fir_ids = [f["fir_id"] for f in firs]
    for _ in range(n):
        victims.append({
            "victim_id": f"VIC-{uuid.uuid4().hex[:8].upper()}",
            "fir_id": random.choice(fir_ids),
            "age": random.randint(5, 80),
            "gender": random.choice(GENDER),
            "district": random.choice(DISTRICTS)
        })
    return victims

# ── Generate Bonds ────────────────────────────────────────────
def generate_bonds(accused_list, n=500):
    bonds = []
    accused_ids = [a["accused_id"] for a in accused_list]
    for _ in range(n):
        signed = random_date(2020, 2024)
        signed_dt = datetime.strptime(signed, "%Y-%m-%d")
        expiry_dt = signed_dt + timedelta(days=365)
        bonds.append({
            "bond_id": f"BOND-{uuid.uuid4().hex[:8].upper()}",
            "accused_id": random.choice(accused_ids),
            "signed_date": signed,
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "status": random.choice(BOND_STATUS)
        })
    return bonds

# ── Generate Court Cases ──────────────────────────────────────
def generate_court_cases(firs, n=500):
    cases = []
    fir_ids = [f["fir_id"] for f in firs]
    docs = ["Chargesheet", "Witness Statement", "Medical Report", "FIR Copy", "None"]
    for _ in range(n):
        cases.append({
            "case_id": f"CASE-{uuid.uuid4().hex[:8].upper()}",
            "fir_id": random.choice(fir_ids),
            "hearing_date": random_date(2024, 2026),
            "status": random.choice(COURT_STATUS),
            "docs_pending": random.choice(docs)
        })
    return cases

# ── Generate CCTV ─────────────────────────────────────────────
def generate_cctv(n=200):
    cameras = []
    owners = ["BBMP", "Private Shop", "ATM", "Apartment", "Traffic Dept", "Bank"]
    for _ in range(n):
        district = random.choice(DISTRICTS)
        cameras.append({
            "camera_id": f"CAM-{uuid.uuid4().hex[:8].upper()}",
            "location_name": fake.street_name(),
            "latitude": random_lat(),
            "longitude": random_lng(),
            "owner": random.choice(owners),
            "district": district,
            "is_active": random.choice(["Yes", "Yes", "Yes", "No"])
        })
    return cameras

# ── Generate Locations ────────────────────────────────────────
def generate_locations():
    locations = []
    for district in DISTRICTS:
        locations.append({
            "location_id": f"LOC-{uuid.uuid4().hex[:8].upper()}",
            "district": district,
            "latitude": random_lat(),
            "longitude": random_lng(),
            "urbanization_index": round(random.uniform(0.3, 0.95), 2),
            "unemployment_rate": round(random.uniform(0.05, 0.35), 2),
            "education_level": round(random.uniform(0.4, 0.95), 2)
        })
    return locations

# ── Write CSV ─────────────────────────────────────────────────
def write_csv(filename, data):
    if not data:
        return
    with open(f"output/{filename}", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {filename} — {len(data)} rows written")



# In generate_data.py, add this:
def generate_case_notes(firs):
    notes = []
    templates = [
        "Investigating officer visited the scene on {date}. Witness {name} stated that the accused was seen near {place} at approximately {time}.",
        "During investigation, CCTV footage from {place} was reviewed. Accused identified as {name} based on footage.",
        "Panchanama conducted at {place}. Recovered items include {items}. Scene secured by {officer}.",
        "Chargesheet prepared against accused {name} under sections {sections}. Case forwarded to court.",
        "Witness {name} recorded statement. Claims accused was known to victim prior to incident."
    ]
    
    items = ["gold chain", "mobile phone", "cash Rs.5000", "vehicle keys", "documents"]
    
    for fir in firs:
        note = random.choice(templates).format(
            date=fir["occurrence_date"],
            name=fake.name(),
            place=fir["occurrence_place"][:30],
            time=fir["occurrence_time"],
            items=random.choice(items),
            officer=fake.name(),
            sections=fir["sections"]
        )
        notes.append({
            "note_id": f"NOTE-{uuid.uuid4().hex[:8].upper()}",
            "fir_id": fir["fir_id"],
            "note_type": random.choice([
                "Investigation Diary",
                "Witness Statement", 
                "Panchanama",
                "Scene Report",
                "Chargesheet Summary"
            ]),
            "content": note,
            "date": fir["date"],
            "officer": fake.name()
        })
    return notes

# ── Main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)

    print("Generating synthetic KSP crime data...")

    firs = generate_firs(2000)
    accused = generate_accused(firs, 1000)
    victims = generate_victims(firs, 1000)
    bonds = generate_bonds(accused, 500)
    cases = generate_court_cases(firs, 500)
    cctv = generate_cctv(200)
    locations = generate_locations()

    write_csv("fir.csv", firs)
    write_csv("accused.csv", accused)
    write_csv("victim.csv", victims)
    write_csv("bond.csv", bonds)
    write_csv("court_case.csv", cases)
    write_csv("cctv.csv", cctv)
    write_csv("location.csv", locations)

    print("\nDone. All files in data/output/")