import argparse
import csv
import hashlib
import os
import sqlite3
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


INPUT_FILES = {
    "fir": "fir.csv",
    "victim": "victim.csv",
    "accused": "accused.csv",
    "court_case": "court_case.csv",
    "bond": "bond.csv",
    "vehicle": "vehicle.csv",
    "evidence": "evidence.csv",
    "witness": "witness.csv",
    "officer": "officer.csv",
    "cctv": "cctv.csv",
    "location": "location.csv",
    "history_sheet": "history_sheet.csv",
    "criminal_network": "criminal_network.csv",
}


OUTPUT_FOLDERS = [
    "incident_reports",
    "case_files",
    "witness_statements",
    "arrest_records",
    "charge_sheets",
    "forensic_reports",
    "history_sheets",
    "daily_case_diary",
    "crime_scene_notes",
]


DEFAULT_TARGETS = {
    "incident_reports": 5000,
    "case_files": 5000,
    "witness_statements": 15000,
    "arrest_records": 3000,
    "charge_sheets": 3500,
    "forensic_reports": 4000,
    "crime_scene_notes": 5000,
    "history_sheets": 1000,
}


OFFICER_TONES = [
    "The case diary reflects a methodical approach, with each development cross-checked against available material records.",
    "The record shows close follow-up on procedural steps, with emphasis on witness corroboration and documentary verification.",
    "The investigation notes indicate a station-level review focused on consistency between the FIR narrative and subsequent recoveries.",
]


WITNESS_STYLES = [
    ("confident", "The witness answered promptly and remained consistent throughout the interaction."),
    ("hesitant", "The witness spoke with some hesitation and repeatedly clarified limits of personal observation."),
    ("emotional", "The witness appeared visibly affected while recounting the events, though the core details remained stable."),
]


CASE_OPENERS = [
    "This case file has been prepared from the station records presently linked to the FIR and related investigation registers.",
    "The following narrative is drawn from the FIR, linked witness material, evidence registers, and related court and custody entries.",
    "This investigation record consolidates the station entries associated with the FIR and presents them in chronological form for review.",
]


def safe(value, default=""):
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() == "nan":
        return default
    return text


def truthy(value):
    return safe(value).lower() in {"true", "1", "yes"}


def deterministic_pick(options, seed_text):
    if not options:
        return ""
    digest = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def ensure_dirs(base_dir):
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    for folder in OUTPUT_FOLDERS:
        (Path(base_dir) / folder).mkdir(parents=True, exist_ok=True)


def build_db(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            db_path = db_path.with_name(f"{db_path.stem}_{stamp}{db_path.suffix}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS fir;
        DROP TABLE IF EXISTS victim;
        DROP TABLE IF EXISTS accused;
        DROP TABLE IF EXISTS court_case;
        DROP TABLE IF EXISTS bond;
        DROP TABLE IF EXISTS vehicle;
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS witness;
        DROP TABLE IF EXISTS officer;
        DROP TABLE IF EXISTS cctv;
        DROP TABLE IF EXISTS location;
        DROP TABLE IF EXISTS history_sheet;
        DROP TABLE IF EXISTS criminal_network;

        CREATE TABLE fir (
            fir_id TEXT PRIMARY KEY, year TEXT, date TEXT, time TEXT, district TEXT, police_station TEXT,
            beat_no TEXT, crime_type TEXT, act TEXT, sections TEXT, occurrence_date TEXT, occurrence_time TEXT,
            occurrence_place TEXT, latitude TEXT, longitude TEXT, complainant_name TEXT, complainant_address TEXT,
            complainant_occupation TEXT, type_of_information TEXT, property_stolen TEXT, estimated_loss TEXT,
            status TEXT, created_at TEXT
        );
        CREATE TABLE victim (
            victim_id TEXT, fir_id TEXT, name TEXT, gender TEXT, age TEXT, occupation TEXT, phone TEXT,
            address TEXT, injury_type TEXT, hospital TEXT, statement_recorded TEXT
        );
        CREATE TABLE accused (
            accused_id TEXT, fir_id TEXT, name TEXT, gender TEXT, age TEXT, occupation TEXT, address TEXT,
            mobile TEXT, aadhaar_last4 TEXT, known_alias TEXT, gang_id TEXT, history_sheeter TEXT, wanted TEXT, status TEXT
        );
        CREATE TABLE court_case (
            case_id TEXT, fir_id TEXT, court_name TEXT, judge TEXT, public_prosecutor TEXT,
            charge_sheet_date TEXT, hearing_date TEXT, verdict TEXT, sentence TEXT, case_status TEXT
        );
        CREATE TABLE bond (
            bond_id TEXT, fir_id TEXT, accused_id TEXT, bond_type TEXT, surety_name TEXT,
            bond_amount TEXT, execution_date TEXT, expiry_date TEXT, status TEXT
        );
        CREATE TABLE vehicle (
            vehicle_id TEXT, owner TEXT, registration_number TEXT, engine_number TEXT, chassis_number TEXT,
            vehicle_type TEXT, color TEXT, manufacturer TEXT, status TEXT, linked_fir TEXT
        );
        CREATE TABLE evidence (
            evidence_id TEXT, fir_id TEXT, type TEXT, description TEXT, forensic_lab TEXT,
            collected_by TEXT, collection_date TEXT, status TEXT
        );
        CREATE TABLE witness (
            witness_id TEXT, fir_id TEXT, name TEXT, age TEXT, gender TEXT, occupation TEXT, statement_date TEXT
        );
        CREATE TABLE officer (
            officer_id TEXT PRIMARY KEY, name TEXT, gender TEXT, rank TEXT, badge_no TEXT, district TEXT,
            police_station TEXT, phone TEXT, email TEXT, active TEXT
        );
        CREATE TABLE cctv (
            camera_id TEXT, owner TEXT, location TEXT, latitude TEXT, longitude TEXT, coverage_angle TEXT,
            resolution TEXT, status TEXT, linked_fir TEXT
        );
        CREATE TABLE location (
            location_id TEXT, district TEXT, taluk TEXT, village_or_ward TEXT, police_station TEXT,
            latitude TEXT, longitude TEXT, jurisdiction_type TEXT
        );
        CREATE TABLE history_sheet (
            history_sheet_id TEXT, accused_id TEXT, name TEXT, police_station TEXT, district TEXT,
            category TEXT, opened_on TEXT, last_reviewed TEXT, fir_count TEXT, risk_score TEXT, remarks TEXT
        );
        CREATE TABLE criminal_network (
            edge_id TEXT, source_accused_id TEXT, target_accused_id TEXT, relationship TEXT, gang_id TEXT,
            strength TEXT, first_seen_fir TEXT
        );
        """
    )
    conn.commit()
    return conn


def load_csv_into_db(conn, table_name, csv_path):
    with open(csv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        placeholders = ",".join(["?"] * len(fieldnames))
        sql = f"INSERT INTO {table_name} ({','.join(fieldnames)}) VALUES ({placeholders})"
        batch = []
        for row in reader:
            batch.append(tuple(safe(row.get(name)) for name in fieldnames))
            if len(batch) >= 2000:
                conn.executemany(sql, batch)
                conn.commit()
                batch.clear()
        if batch:
            conn.executemany(sql, batch)
            conn.commit()


def create_indexes(conn):
    cur = conn.cursor()
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_victim_fir ON victim(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_accused_fir ON accused(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_court_fir ON court_case(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_bond_fir ON bond(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_vehicle_fir ON vehicle(linked_fir)",
        "CREATE INDEX IF NOT EXISTS idx_evidence_fir ON evidence(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_witness_fir ON witness(fir_id)",
        "CREATE INDEX IF NOT EXISTS idx_cctv_fir ON cctv(linked_fir)",
        "CREATE INDEX IF NOT EXISTS idx_history_accused ON history_sheet(accused_id)",
        "CREATE INDEX IF NOT EXISTS idx_network_source ON criminal_network(source_accused_id)",
        "CREATE INDEX IF NOT EXISTS idx_network_target ON criminal_network(target_accused_id)",
        "CREATE INDEX IF NOT EXISTS idx_officer_station ON officer(police_station)",
        "CREATE INDEX IF NOT EXISTS idx_officer_district ON officer(district)",
        "CREATE INDEX IF NOT EXISTS idx_location_station ON location(police_station)",
    ]
    for statement in statements:
        cur.execute(statement)
    conn.commit()


def fetch_all(conn, sql, params=()):
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def choose_investigating_officer(conn, fir_row):
    station_matches = fetch_all(
        conn,
        "SELECT * FROM officer WHERE police_station = ? ORDER BY officer_id LIMIT 5",
        (safe(fir_row["police_station"]),),
    )
    district_matches = fetch_all(
        conn,
        "SELECT * FROM officer WHERE district = ? ORDER BY officer_id LIMIT 5",
        (safe(fir_row["district"]),),
    )
    pool = station_matches or district_matches or fetch_all(conn, "SELECT * FROM officer ORDER BY officer_id LIMIT 10")
    officer = pool[int(hashlib.md5(safe(fir_row["fir_id"]).encode("utf-8")).hexdigest()[:8], 16) % len(pool)]
    return officer


def fetch_bundle(conn, fir_row):
    fir_id = safe(fir_row["fir_id"])
    accused = fetch_all(conn, "SELECT * FROM accused WHERE fir_id = ? ORDER BY accused_id", (fir_id,))
    witnesses = fetch_all(conn, "SELECT * FROM witness WHERE fir_id = ? ORDER BY witness_id", (fir_id,))
    victims = fetch_all(conn, "SELECT * FROM victim WHERE fir_id = ? ORDER BY victim_id", (fir_id,))
    evidence = fetch_all(conn, "SELECT * FROM evidence WHERE fir_id = ? ORDER BY evidence_id", (fir_id,))
    court_cases = fetch_all(conn, "SELECT * FROM court_case WHERE fir_id = ? ORDER BY case_id", (fir_id,))
    bonds = fetch_all(conn, "SELECT * FROM bond WHERE fir_id = ? ORDER BY bond_id", (fir_id,))
    vehicles = fetch_all(conn, "SELECT * FROM vehicle WHERE linked_fir = ? ORDER BY vehicle_id", (fir_id,))
    cameras = fetch_all(conn, "SELECT * FROM cctv WHERE linked_fir = ? ORDER BY camera_id", (fir_id,))
    location = conn.execute(
        "SELECT * FROM location WHERE police_station = ? LIMIT 1",
        (safe(fir_row["police_station"]),),
    ).fetchone()
    location = dict(location) if location else {}
    officer = choose_investigating_officer(conn, fir_row)
    histories = []
    network_edges = []
    for accused_row in accused:
        histories.extend(fetch_all(conn, "SELECT * FROM history_sheet WHERE accused_id = ? ORDER BY history_sheet_id", (safe(accused_row["accused_id"]),)))
        network_edges.extend(
            fetch_all(
                conn,
                "SELECT * FROM criminal_network WHERE source_accused_id = ? OR target_accused_id = ? ORDER BY edge_id LIMIT 15",
                (safe(accused_row["accused_id"]), safe(accused_row["accused_id"])),
            )
        )
    return {
        "fir": dict(fir_row),
        "victims": victims,
        "accused": accused,
        "witnesses": witnesses,
        "evidence": evidence,
        "court_cases": court_cases,
        "bonds": bonds,
        "vehicles": vehicles,
        "cameras": cameras,
        "location": location,
        "officer": officer,
        "histories": histories,
        "network_edges": network_edges,
    }


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.strip() + "\n")


def victim_summary(victims):
    if not victims:
        return "No linked victim entry was available in the current extracts."
    lines = []
    for victim in victims:
        lines.append(
            f"{safe(victim['name'])}, {safe(victim['age'])} years, {safe(victim['occupation'])}, injury noted as {safe(victim['injury_type'], 'not specified')}."
        )
    return " ".join(lines)


def accused_summary(accused_rows):
    if not accused_rows:
        return "No accused person has been linked in the present records."
    bits = []
    for row in accused_rows:
        alias = safe(row["known_alias"])
        alias_text = f", alias {alias}" if alias else ""
        bits.append(
            f"{safe(row['name'])}{alias_text}, aged {safe(row['age'])}, status {safe(row['status'])}, history sheeter {safe(row['history_sheeter'], 'false')}."
        )
    return " ".join(bits)


def evidence_summary(evidence_rows):
    if not evidence_rows:
        return "No physical or digital evidence has yet been linked to the FIR."
    return " ".join(
        f"{safe(item['type'])} recorded under evidence ID {safe(item['evidence_id'])} with status {safe(item['status'])}."
        for item in evidence_rows[:8]
    )


def witness_summary(witness_rows):
    if not witness_rows:
        return "No witness statement is currently linked."
    return " ".join(
        f"{safe(item['name'])}, occupation {safe(item['occupation'])}, statement dated {safe(item['statement_date'])}."
        for item in witness_rows[:6]
    )


def cctv_summary(camera_rows):
    if not camera_rows:
        return "No CCTV asset is linked in the available records."
    return " ".join(
        f"Camera {safe(item['camera_id'])} at {safe(item['location'])} owned by {safe(item['owner'])} is marked {safe(item['status'])}."
        for item in camera_rows[:4]
    )


def vehicle_summary(vehicle_rows):
    if not vehicle_rows:
        return "No linked vehicle record is presently available."
    return " ".join(
        f"Vehicle {safe(item['registration_number'])}, a {safe(item['color'])} {safe(item['manufacturer'])} {safe(item['vehicle_type'])}, is marked {safe(item['status'])}."
        for item in vehicle_rows[:4]
    )


def build_incident_report(bundle):
    fir = bundle["fir"]
    officer = bundle["officer"]
    victims = bundle["victims"]
    location = bundle["location"]
    observations = deterministic_pick(
        [
            "The scene details in the FIR show immediate concern for preservation of place of occurrence and separation of bystanders.",
            "Initial station handling reflects prompt registration and a preliminary effort to note visible disturbance, access points, and property condition.",
            "The first response record indicates attention to victim safety, scene control, and identification of immediate leads.",
        ],
        safe(fir["fir_id"]) + "incident",
    )
    return f"""
Incident Number: {safe(fir['fir_id'])}
Date: {safe(fir['date'])}
Time: {safe(fir['time'])}
Police Station: {safe(fir['police_station'])}
Investigating Officer: {safe(officer['rank'])} {safe(officer['name'])} ({safe(officer['badge_no'])})

Summary of Incident:
The FIR records a case of {safe(fir['crime_type'])} reported within the jurisdiction of {safe(fir['police_station'])}. The occurrence is noted at {safe(fir['occurrence_place'])} on {safe(fir['occurrence_date'])} at about {safe(fir['occurrence_time'])}. The information was received as {safe(fir['type_of_information']).lower()} and registered under {safe(fir['act'])}, sections {safe(fir['sections'])}.

Victim Details:
{victim_summary(victims)}

Location:
District: {safe(fir['district'])}
Beat Number: {safe(fir['beat_no'])}
Recorded Coordinates: {safe(fir['latitude'])}, {safe(fir['longitude'])}
Taluk/Ward Reference: {safe(location.get('taluk'))} / {safe(location.get('village_or_ward'))}

Initial Observations:
{observations} {safe(fir['complainant_name'])} is shown as complainant, with address recorded as {safe(fir['complainant_address'])}.

Property Loss:
Property/Subject: {safe(fir['property_stolen'], 'Not recorded')}
Estimated Loss: {safe(fir['estimated_loss'], '0')}

IPC/BNS Sections:
{safe(fir['sections'])}

Actions Taken:
FIR registration completed, complainant details entered, linked witnesses and evidence reviewed from available records, and investigation marked to the above officer for follow-up.

Status:
{safe(fir['status'])}
"""


def build_case_file(bundle):
    fir = bundle["fir"]
    officer = bundle["officer"]
    court = bundle["court_cases"][:1]
    opener = deterministic_pick(CASE_OPENERS, safe(fir["fir_id"]) + "case")
    paragraphs = [
        opener,
        f"The matter originates from FIR {safe(fir['fir_id'])}, registered at {safe(fir['police_station'])} in {safe(fir['district'])} district. The entry classifies the occurrence as {safe(fir['crime_type'])} and records the occurrence place as {safe(fir['occurrence_place'])}. The station record shows that information was received through {safe(fir['type_of_information']).lower()}, after which formal registration was carried out under {safe(fir['act'])} and the sections noted as {safe(fir['sections'])}.",
        f"In the background available from the records, the complainant is {safe(fir['complainant_name'])}, whose occupation is entered as {safe(fir['complainant_occupation'])}. The incident date and time are reflected as {safe(fir['occurrence_date'])} at about {safe(fir['occurrence_time'])}. The later registration timestamp on the FIR is {safe(fir['date'])} {safe(fir['time'])}. This timing pattern is relevant because it frames the interval between occurrence, complaint, scene control, witness contact, and evidence handling.",
        f"The victim profile emerging from the linked victim table is as follows: {victim_summary(bundle['victims'])} The injury and hospital fields, where available, assist in distinguishing between bodily harm, financial loss, and property-centric offences. Where the injury field is recorded as financial loss or none, the focus of inquiry naturally shifts toward property movement, transaction trail, device trail, or corroborative witness evidence.",
        f"The suspect profile drawn from the accused register is: {accused_summary(bundle['accused'])} When gang or history-sheet flags are present, the records suggest that the station may need to compare the present FIR with prior behavioural patterns, known associates, and movement intelligence. Where an accused remains unlinked, the file reflects an investigation that is still dependent on leads rather than formal attribution.",
        f"Evidence presently linked to the case consists of the following: {evidence_summary(bundle['evidence'])} These entries are material because they show whether the investigation has remained at the level of complaint verification or has moved into documented recovery, seizure, laboratory referral, or device examination.",
        f"The witness position is summarized in the linked records as: {witness_summary(bundle['witnesses'])} The content and timing of witness statements help measure whether the narrative is immediate, delayed, corroborative, partial, or uncertain. A witness who speaks soon after the occurrence may add immediacy, while a later statement may add context after local discussion or reflection.",
        f"CCTV and surveillance material are reflected as follows: {cctv_summary(bundle['cameras'])} Vehicle-linked records, if any, are: {vehicle_summary(bundle['vehicles'])} These two sources are often operationally important because they support route reconstruction, identity confirmation, or recovery tracing without requiring the file to speculate beyond what the registers already show.",
        f"The investigating officer allocated from the station side for this case narrative is {safe(officer['rank'])} {safe(officer['name'])}, badge {safe(officer['badge_no'])}. {deterministic_pick(OFFICER_TONES, safe(fir['fir_id']) + 'tone')} This officer narrative is based on the available station and district officer register and is used here to maintain a consistent paperwork chain inside the generated document set.",
        f"Investigation progress can also be read from procedural side tables. Court linkage currently stands as {safe(court[0]['case_status']) if court else 'no linked court case in current extract'}. Bond linkage count is {len(bundle['bonds'])}. History-sheet linkage count against accused persons is {len(bundle['histories'])}. Network edges associated with linked accused count {len(bundle['network_edges'])}, which may indicate known associates, prior co-accused connections, or linked criminal movement requiring separate verification.",
        f"At the present stage, the station status recorded on the FIR remains {safe(fir['status'])}. If the court record exists, the case table further notes charge sheet date, hearing date, and any verdict details. This combined view is useful because a case may appear active at station level even while portions of the prosecution process are already scheduled or under review. Conversely, some cases remain fact-finding matters where the documentary volume is still building.",
        f"In summary, this case file does not invent facts beyond the linked data. It shows a complaint of {safe(fir['crime_type'])}, anchored to the recorded place, linked persons, available evidence, witness statements, and procedural follow-up. The current paperwork indicates that the investigation should continue through evidence verification, witness corroboration, review of surveillance or vehicle trace where present, and court coordination where a prosecution record has already been opened.",
    ]
    return "\n\n".join(paragraphs)


def build_investigation_summary(bundle):
    fir = bundle["fir"]
    officer = bundle["officer"]
    return f"""
Investigation Summary for {safe(fir['fir_id'])}

Investigating Officer:
{safe(officer['rank'])} {safe(officer['name'])}, Badge {safe(officer['badge_no'])}

Background:
The case concerns {safe(fir['crime_type'])} reported at {safe(fir['occurrence_place'])} within {safe(fir['police_station'])}.

Key Linked Persons:
Victims: {", ".join(safe(v['name']) for v in bundle['victims']) or 'Nil'}
Accused: {", ".join(safe(a['name']) for a in bundle['accused']) or 'Nil'}
Witnesses: {", ".join(safe(w['name']) for w in bundle['witnesses']) or 'Nil'}

Material Collected:
{evidence_summary(bundle['evidence'])}

Procedural Position:
Court Cases: {len(bundle['court_cases'])}
Bond Entries: {len(bundle['bonds'])}
Linked Cameras: {len(bundle['cameras'])}
Linked Vehicles: {len(bundle['vehicles'])}

Current Assessment:
The available records support continuation of inquiry in line with the present FIR status of {safe(fir['status'])}. The station record should be read together with witness, evidence, and court tables for any next procedural step.
"""


def build_crime_scene_note(bundle):
    fir = bundle["fir"]
    weather = deterministic_pick(
        ["Dry weather at time of visit.", "Cloud cover present with moderate ambient moisture.", "Warm conditions with normal evening visibility."],
        safe(fir["fir_id"]) + "weather",
    )
    lighting = "Street and ambient commercial lighting available." if safe(fir["crime_type"]) not in {"Burglary", "Vehicle Theft"} else "Lighting was limited and required close inspection."
    entry = deterministic_pick(
        ["Likely approach through the main public access side.", "No forced structural entry was immediately obvious from the recorded note.", "Approach appears consistent with normal public movement in the area."],
        safe(fir["fir_id"]) + "entry",
    )
    exit_point = deterministic_pick(
        ["Departure path likely merged into routine local traffic.", "Exit path could not be fixed from the station note alone.", "The route away from the scene appears open toward the adjoining road network."],
        safe(fir["fir_id"]) + "exit",
    )
    blood = "Visible blood evidence is not specifically recorded in linked material." if safe(fir["crime_type"]) not in {"Assault", "Road Accident"} else "Possible blood-related scene relevance should be read with medical and evidence tables."
    weapons = "Weapon reference appears in linked evidence." if any(safe(ev["type"]) == "Weapon" for ev in bundle["evidence"]) else "No explicit weapon recovery is linked in the evidence register."
    return f"""
Crime Scene Note: {safe(fir['fir_id'])}

Location:
{safe(fir['occurrence_place'])}, {safe(fir['police_station'])}, {safe(fir['district'])}

Date/Time of Occurrence:
{safe(fir['occurrence_date'])} at {safe(fir['occurrence_time'])}

Weather:
{weather}

Lighting:
{lighting}

Entry Point:
{entry}

Exit Point:
{exit_point}

Objects Observed:
The available record identifies the subject matter/property as {safe(fir['property_stolen'], 'not specifically entered')}. Nearby scene significance should be correlated with witness and CCTV records where available.

Blood:
{blood}

Weapons:
{weapons}

Footprints:
No distinct footprint observation is preserved in the CSV extracts; scene interpretation remains limited to recorded evidence and witness data.

Vehicle Tracks:
{vehicle_summary(bundle['vehicles'])}
"""


def build_witness_statement(bundle, witness_row, idx):
    fir = bundle["fir"]
    officer = bundle["officer"]
    style_name, style_note = WITNESS_STYLES[(idx - 1) % len(WITNESS_STYLES)]
    prompts = {
        "confident": "State clearly what you personally saw or heard.",
        "hesitant": "Tell me only what you are certain about and mention where you are unsure.",
        "emotional": "Take your time and describe what happened in your own words.",
    }
    response_templates = {
        "confident": f"I am {safe(witness_row['name'])}. I was present near {safe(fir['occurrence_place'])} around the time mentioned. I can identify the general sequence of events related to this {safe(fir['crime_type']).lower()} matter and I have stated only what I directly observed.",
        "hesitant": f"My name is {safe(witness_row['name'])}. I was in the area, but I cannot claim to have seen every detail. I remember movement near {safe(fir['occurrence_place'])} and I can confirm the timing generally, though some parts are based on what drew my attention afterward.",
        "emotional": f"I am {safe(witness_row['name'])}. The incident at {safe(fir['occurrence_place'])} was upsetting to witness. I remember the victim side of the situation first and then noticed the disturbance connected with the reported {safe(fir['crime_type']).lower()}.",
    }
    follow_up = f"The person I can refer to from memory is {safe(bundle['victims'][0]['name']) if bundle['victims'] else safe(fir['complainant_name'])}. I gave my statement on {safe(witness_row['statement_date'])} and I understand it is being used for investigation."
    return f"""
Witness Statement
FIR: {safe(fir['fir_id'])}
Police Station: {safe(fir['police_station'])}
Recording Officer: {safe(officer['rank'])} {safe(officer['name'])}
Witness: {safe(witness_row['name'])}, {safe(witness_row['age'])} years, {safe(witness_row['occupation'])}

Officer: Please confirm your name and relation to the incident.
Witness: {response_templates[style_name]}

Officer: {prompts[style_name]}
Witness: {follow_up}

Officer: Did anyone influence your version before this statement?
Witness: No external pressure has been stated by me. I have narrated the matter according to my recollection.

Officer Note:
{style_note}
"""


def build_arrest_record(bundle, accused_row):
    fir = bundle["fir"]
    officer = bundle["officer"]
    bond_rows = [row for row in bundle["bonds"] if safe(row["accused_id"]) == safe(accused_row["accused_id"])]
    evidence_list = ", ".join(safe(ev["type"]) for ev in bundle["evidence"][:4]) or "No seizure item specifically linked at this stage"
    arrest_date = safe(bond_rows[0]["execution_date"]) if bond_rows else safe(fir["date"])
    custody = safe(accused_row["status"])
    return f"""
Arrest Record

FIR: {safe(fir['fir_id'])}
Accused: {safe(accused_row['name'])} ({safe(accused_row['accused_id'])})
Arrest Date: {arrest_date}
Officer: {safe(officer['rank'])} {safe(officer['name'])}
Reason:
Arrest/procedural custody action shown in relation to the investigation of {safe(fir['crime_type'])} under sections {safe(fir['sections'])}.

Legal Sections:
{safe(fir['sections'])}

Items Seized:
{evidence_list}

Rights Explained:
The record notes that the accused was informed of the grounds of action and procedural rights in the course of arrest processing.

Medical Examination:
Medical examination to be read as completed/referred as per standard arrest handling procedure; no contradictory field is present in current linked CSV records.

Custody Status:
{custody}
"""


def build_charge_sheet(bundle):
    fir = bundle["fir"]
    court = bundle["court_cases"][0]
    officer = bundle["officer"]
    evidence_list = "\n".join(f"- {safe(ev['evidence_id'])}: {safe(ev['type'])}, {safe(ev['status'])}" for ev in bundle["evidence"][:12]) or "- Nil"
    witness_list = "\n".join(f"- {safe(w['name'])}, statement dated {safe(w['statement_date'])}" for w in bundle["witnesses"][:20]) or "- Nil"
    accused_list = ", ".join(safe(a["name"]) for a in bundle["accused"]) or "Unknown/Not linked"
    return f"""
Charge Sheet

Court:
{safe(court['court_name'])}

FIR:
{safe(fir['fir_id'])}

Accused:
{accused_list}

Charges:
{safe(fir['act'])}, Sections {safe(fir['sections'])}

Evidence List:
{evidence_list}

Witness List:
{witness_list}

Officer Opinion:
Upon review of the linked records, sufficient material exists to place the above facts before the court for consideration in accordance with law. The charge sheet relies on the FIR, linked witness statements, evidence register, and any supporting surveillance or vehicle records available in the case extract.

Recommendation:
Proceed in terms of the case status shown as {safe(court['case_status'])} and list the matter for further judicial scrutiny.

Filed By:
{safe(officer['rank'])} {safe(officer['name'])}
"""


def build_forensic_report(bundle):
    fir = bundle["fir"]
    evidence_rows = bundle["evidence"]
    lab = safe(next((ev["forensic_lab"] for ev in evidence_rows if safe(ev["forensic_lab"])), ""), "Regional Forensic Laboratory")
    received = ", ".join(f"{safe(ev['evidence_id'])} ({safe(ev['type'])})" for ev in evidence_rows[:8])
    has_mobile = any(safe(ev["type"]) == "Mobile phone" for ev in evidence_rows)
    has_weapon = any(safe(ev["type"]) == "Weapon" for ev in evidence_rows)
    return f"""
Forensic Report

Laboratory:
{lab}

FIR:
{safe(fir['fir_id'])}

Evidence Received:
{received or 'No lab-marked exhibit listed in the current extract.'}

Fingerprint Analysis:
No conclusive fingerprint narrative is separately stored in the CSV extract. Examination status should be read with the linked evidence status entries.

DNA Analysis:
DNA-specific result is not independently recorded in the available dataset.

Blood Analysis:
No separate blood-analysis result field is present in the linked tables.

Ballistics:
{"Weapon-linked exhibits may require ballistic opinion." if has_weapon else "No clear ballistic exhibit is linked in the current evidence rows."}

Mobile Forensics:
{"Mobile or digital device evidence is present and may support device-level extraction or communication review." if has_mobile else "No mobile-forensics-specific exhibit is clearly linked for this FIR."}

Conclusion:
The forensic summary is limited to the exhibits and statuses actually connected to the FIR. Present linked evidence suggests a {safe(fir['crime_type']).lower()} inquiry with procedural reliance on documented seizure and laboratory routing where available.
"""


def build_history_sheet(bundle, history_row, related_accused):
    networks = [
        row for row in bundle["network_edges"]
        if safe(row["source_accused_id"]) == safe(related_accused["accused_id"])
        or safe(row["target_accused_id"]) == safe(related_accused["accused_id"])
    ]
    associates = ", ".join(
        {
            safe(row["target_accused_id"]) if safe(row["source_accused_id"]) == safe(related_accused["accused_id"]) else safe(row["source_accused_id"])
            for row in networks[:10]
        }
    )
    gang = safe(related_accused["gang_id"], "Not linked")
    return f"""
History Sheet

History Sheet ID:
{safe(history_row['history_sheet_id'])}

Accused:
{safe(related_accused['name'])} ({safe(related_accused['accused_id'])})

Previous FIRs:
{safe(history_row['remarks'])}

Known Associates:
{associates or 'No associate edge captured in current network extract.'}

Gang Affiliation:
{gang}

Known Modus Operandi:
Category noted as {safe(history_row['category'])}; present FIR linkage should be compared with the pattern reflected in the history register.

Known Locations:
{safe(history_row['police_station'])}, {safe(history_row['district'])}

Risk Level:
Risk Score {safe(history_row['risk_score'])}
"""


def build_case_diary(bundle):
    fir = bundle["fir"]
    officer = bundle["officer"]
    base_date = datetime.strptime(safe(fir["date"]), "%Y-%m-%d")
    steps = [
        f"Day 1 - {base_date.date()}: FIR reviewed by {safe(officer['rank'])} {safe(officer['name'])}; complainant details cross-checked; place of occurrence and beat details noted.",
        f"Day 2 - {(base_date + timedelta(days=1)).date()}: Witness availability reviewed; linked witness table checked; station notes aligned with occurrence timing and property/loss fields.",
        f"Day 3 - {(base_date + timedelta(days=2)).date()}: Evidence register examined; seizure entries and collection dates compared with the FIR allegations.",
    ]
    if bundle["cameras"]:
        steps.append(f"Day 4 - {(base_date + timedelta(days=3)).date()}: CCTV linkage examined for {len(bundle['cameras'])} camera record(s) connected to the FIR.")
    if bundle["accused"]:
        steps.append(f"Day 5 - {(base_date + timedelta(days=4)).date()}: Accused profiles reviewed; custody and history-sheeter indicators checked against available records.")
    if bundle["court_cases"]:
        steps.append(f"Day 6 - {(base_date + timedelta(days=5)).date()}: Court case linkage reviewed with status {safe(bundle['court_cases'][0]['case_status'])}.")
    return "Daily Case Diary\n\nFIR: {}\nPolice Station: {}\n\n{}".format(
        safe(fir["fir_id"]),
        safe(fir["police_station"]),
        "\n".join(steps),
    )


def should_create_charge_sheet(bundle):
    return bool(bundle["court_cases"])


def should_create_arrest(bundle):
    return any(safe(row["status"]) in {"Arrested", "Remanded"} for row in bundle["accused"])


def should_create_forensic(bundle):
    return bool(bundle["evidence"])


def related_history_rows(bundle):
    history_by_accused = defaultdict(list)
    for row in bundle["histories"]:
        history_by_accused[safe(row["accused_id"])].append(row)
    output = []
    for accused in bundle["accused"]:
        if truthy(accused["history_sheeter"]):
            output.extend((history_row, accused) for history_row in history_by_accused.get(safe(accused["accused_id"]), []))
    return output


def filename_token(fir_id):
    return safe(fir_id).replace("-", "")


def generate_documents(conn, output_dir, targets, fir_limit):
    ensure_dirs(output_dir)
    counters = defaultdict(int)
    fir_rows = conn.execute("SELECT * FROM fir ORDER BY fir_id")
    processed_firs = 0

    for fir_row in fir_rows:
        if processed_firs >= fir_limit:
            break
        if all(counters[key] >= targets[key] for key in targets):
            break

        bundle = fetch_bundle(conn, fir_row)
        token = filename_token(bundle["fir"]["fir_id"])

        if counters["incident_reports"] < targets["incident_reports"]:
            write_text(Path(output_dir) / "incident_reports" / f"{token}_incident.txt", build_incident_report(bundle))
            counters["incident_reports"] += 1

        if counters["case_files"] < targets["case_files"]:
            write_text(Path(output_dir) / "case_files" / f"{token}_casefile.txt", build_case_file(bundle))
            write_text(Path(output_dir) / "case_files" / f"{token}_summary.txt", build_investigation_summary(bundle))
            counters["case_files"] += 1

        if counters["crime_scene_notes"] < targets["crime_scene_notes"]:
            write_text(Path(output_dir) / "crime_scene_notes" / f"{token}_scene.txt", build_crime_scene_note(bundle))
            counters["crime_scene_notes"] += 1

        write_text(Path(output_dir) / "daily_case_diary" / f"{token}_diary.txt", build_case_diary(bundle))

        if should_create_charge_sheet(bundle) and counters["charge_sheets"] < targets["charge_sheets"]:
            write_text(Path(output_dir) / "charge_sheets" / f"{token}_charge_sheet.txt", build_charge_sheet(bundle))
            counters["charge_sheets"] += 1

        if should_create_forensic(bundle) and counters["forensic_reports"] < targets["forensic_reports"]:
            write_text(Path(output_dir) / "forensic_reports" / f"{token}_forensic.txt", build_forensic_report(bundle))
            counters["forensic_reports"] += 1

        if should_create_arrest(bundle) and counters["arrest_records"] < targets["arrest_records"]:
            arrest_accused = next(row for row in bundle["accused"] if safe(row["status"]) in {"Arrested", "Remanded"})
            write_text(Path(output_dir) / "arrest_records" / f"{token}_arrest.txt", build_arrest_record(bundle, arrest_accused))
            counters["arrest_records"] += 1

        if counters["witness_statements"] < targets["witness_statements"]:
            for idx, witness_row in enumerate(bundle["witnesses"], start=1):
                if counters["witness_statements"] >= targets["witness_statements"]:
                    break
                write_text(
                    Path(output_dir) / "witness_statements" / f"{token}_witness_{idx:02d}.txt",
                    build_witness_statement(bundle, witness_row, idx),
                )
                counters["witness_statements"] += 1

        if counters["history_sheets"] < targets["history_sheets"]:
            for idx, (history_row, accused_row) in enumerate(related_history_rows(bundle), start=1):
                if counters["history_sheets"] >= targets["history_sheets"]:
                    break
                write_text(
                    Path(output_dir) / "history_sheets" / f"{token}_history_{idx:02d}.txt",
                    build_history_sheet(bundle, history_row, accused_row),
                )
                counters["history_sheets"] += 1

        processed_firs += 1

    return counters, processed_firs


def parse_args():
    parser = argparse.ArgumentParser(description="Generate police investigation text documents from existing synthetic CSV data.")
    parser.add_argument("--input-dir", default=str(Path(__file__).resolve().parent / "output"), help="Directory containing generated CSV files.")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / "documents"), help="Directory for generated document text files.")
    parser.add_argument(
        "--db-path",
        default=str(Path(tempfile.gettempdir()) / "ksp_document_index.sqlite"),
        help="SQLite path used to index CSV relationships. Defaults to the system temp directory.",
    )
    parser.add_argument(
        "--fir-limit",
        type=int,
        default=20000,
        help="Maximum FIR records to scan while filling document targets. Keep this above 5000 if you want higher witness/arrest/history counts.",
    )
    parser.add_argument("--incident-target", type=int, default=DEFAULT_TARGETS["incident_reports"])
    parser.add_argument("--case-target", type=int, default=DEFAULT_TARGETS["case_files"])
    parser.add_argument("--witness-target", type=int, default=DEFAULT_TARGETS["witness_statements"])
    parser.add_argument("--arrest-target", type=int, default=DEFAULT_TARGETS["arrest_records"])
    parser.add_argument("--charge-target", type=int, default=DEFAULT_TARGETS["charge_sheets"])
    parser.add_argument("--forensic-target", type=int, default=DEFAULT_TARGETS["forensic_reports"])
    parser.add_argument("--scene-target", type=int, default=DEFAULT_TARGETS["crime_scene_notes"])
    parser.add_argument("--history-target", type=int, default=DEFAULT_TARGETS["history_sheets"])
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    conn = build_db(args.db_path)
    try:
        for table_name, filename in INPUT_FILES.items():
            load_csv_into_db(conn, table_name, input_dir / filename)
        create_indexes(conn)

        counters, processed_firs = generate_documents(
            conn,
            output_dir,
            {
                "incident_reports": args.incident_target,
                "case_files": args.case_target,
                "witness_statements": args.witness_target,
                "arrest_records": args.arrest_target,
                "charge_sheets": args.charge_target,
                "forensic_reports": args.forensic_target,
                "crime_scene_notes": args.scene_target,
                "history_sheets": args.history_target,
            },
            args.fir_limit,
        )
        print(f"Processed FIRs: {processed_firs}")
        for key in sorted(counters):
            print(f"{key}: {counters[key]}")
        print(f"Documents written under: {output_dir.resolve()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
