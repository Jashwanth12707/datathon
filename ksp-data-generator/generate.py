import argparse
import json
from pathlib import Path
from time import perf_counter

import pandas as pd

from config import COUNTS, OUTPUT_DIR, RANDOM_SEED
from generators import (
    accused_generator,
    bond_generator,
    cctv_generator,
    court_generator,
    evidence_generator,
    fir_generator,
    gang_generator,
    history_generator,
    location_generator,
    network_generator,
    officer_generator,
    station_generator,
    vehicle_generator,
    victim_generator,
    witness_generator,
)
from generators.utils import ensure_dir, write_rows


GENERATOR_PLAN = [
    ("location.csv", location_generator.FIELDS, location_generator.rows, ("station",)),
    ("station.csv", station_generator.FIELDS, station_generator.rows, ("station",)),
    ("officer.csv", officer_generator.FIELDS, officer_generator.rows, ("officer",)),
    ("gang.csv", gang_generator.FIELDS, gang_generator.rows, ("gang",)),
    ("fir.csv", fir_generator.FIELDS, fir_generator.rows, ("fir",)),
    ("victim.csv", victim_generator.FIELDS, victim_generator.rows, ("victim", "fir")),
    ("accused.csv", accused_generator.FIELDS, accused_generator.rows, ("accused", "fir", "gang")),
    ("evidence.csv", evidence_generator.FIELDS, evidence_generator.rows, ("evidence", "fir", "officer")),
    ("witness.csv", witness_generator.FIELDS, witness_generator.rows, ("witness", "fir")),
    ("court_case.csv", court_generator.FIELDS, court_generator.rows, ("court", "fir")),
    ("vehicle.csv", vehicle_generator.FIELDS, vehicle_generator.rows, ("vehicle", "fir")),
    ("cctv.csv", cctv_generator.FIELDS, cctv_generator.rows, ("cctv", "fir")),
    ("bond.csv", bond_generator.FIELDS, bond_generator.rows, ("bond", "fir", "accused")),
    ("history_sheet.csv", history_generator.FIELDS, history_generator.rows, ("history", "accused")),
    ("criminal_network.csv", network_generator.FIELDS, network_generator.rows, ("network", "accused", "gang", "fir")),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic Karnataka State Police relational crime datasets.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Directory where CSV files will be written.")
    parser.add_argument("--scale", type=float, default=1.0, help="Multiply all configured counts by this value.")
    parser.add_argument("--small", action="store_true", help="Generate a tiny dataset for smoke testing.")
    for key in sorted(COUNTS):
        parser.add_argument(f"--{key}", type=int, default=None, help=f"Override {key} row count.")
    return parser.parse_args()


def resolve_counts(args):
    if args.small:
        counts = {
            "fir": 1000,
            "victim": 850,
            "accused": 300,
            "evidence": 1200,
            "witness": 900,
            "court": 300,
            "vehicle": 400,
            "cctv": 120,
            "officer": 160,
            "station": 80,
            "bond": 220,
            "gang": 40,
            "history": 120,
            "network": 600,
        }
    else:
        counts = {key: max(0, int(value * args.scale)) for key, value in COUNTS.items()}
    for key in counts:
        override = getattr(args, key)
        if override is not None:
            counts[key] = override
    return counts


def call_generator(row_function, keys, counts):
    values = [counts[key] for key in keys]
    return row_function(*values)


def generate_all(output_dir, counts):
    ensure_dir(output_dir)
    manifest = []
    start = perf_counter()

    for filename, fields, row_function, keys in GENERATOR_PLAN:
        count_key = keys[0]
        total = counts[count_key]
        path = Path(output_dir) / filename
        rows = call_generator(row_function, keys, counts)
        write_rows(path, fields, rows, total=total, description=filename)
        manifest.append({"file": filename, "rows": total, "columns": len(fields)})

    elapsed = round(perf_counter() - start, 2)
    manifest_path = Path(output_dir) / "_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "random_seed": RANDOM_SEED,
                "elapsed_seconds": elapsed,
                "counts": counts,
                "files": manifest,
            },
            handle,
            indent=2,
        )

    summary = pd.DataFrame(manifest)
    print(summary.to_string(index=False))
    print(f"\nGenerated {sum(item['rows'] for item in manifest):,} rows in {elapsed}s at {Path(output_dir).resolve()}")


def main():
    args = parse_args()
    counts = resolve_counts(args)
    generate_all(args.output_dir, counts)


if __name__ == "__main__":
    main()

