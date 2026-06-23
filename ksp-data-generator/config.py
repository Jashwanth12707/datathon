from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("KSP_OUTPUT_DIR", BASE_DIR / "output"))
RANDOM_SEED = int(os.getenv("KSP_RANDOM_SEED", "42"))
CSV_BATCH_SIZE = int(os.getenv("KSP_CSV_BATCH_SIZE", "10000"))


COUNTS = {
    "fir": int(os.getenv("KSP_FIR_COUNT", "100000")),
    "victim": int(os.getenv("KSP_VICTIM_COUNT", "85000")),
    "accused": int(os.getenv("KSP_ACCUSED_COUNT", "30000")),
    "evidence": int(os.getenv("KSP_EVIDENCE_COUNT", "200000")),
    "witness": int(os.getenv("KSP_WITNESS_COUNT", "120000")),
    "court": int(os.getenv("KSP_COURT_COUNT", "40000")),
    "vehicle": int(os.getenv("KSP_VEHICLE_COUNT", "50000")),
    "cctv": int(os.getenv("KSP_CAMERA_COUNT", "10000")),
    "officer": int(os.getenv("KSP_OFFICER_COUNT", "8000")),
    "station": int(os.getenv("KSP_STATION_COUNT", "420")),
    "bond": int(os.getenv("KSP_BOND_COUNT", "25000")),
    "gang": int(os.getenv("KSP_GANG_COUNT", "450")),
    "history": int(os.getenv("KSP_HISTORY_COUNT", "18000")),
    "network": int(os.getenv("KSP_NETWORK_COUNT", "60000")),
}


START_YEAR = int(os.getenv("KSP_START_YEAR", "2018"))
END_YEAR = int(os.getenv("KSP_END_YEAR", "2026"))


FIR_ID_PREFIX = os.getenv("KSP_FIR_ID_PREFIX", "FIR")
ID_PAD = int(os.getenv("KSP_ID_PAD", "9"))
