import argparse
import json
import os
import time
from pathlib import Path

from zcatalyst_sdk import initialize_app


LOAD_ORDER = [
    ("location.csv", "location"),
    ("station.csv", "station"),
    ("officer.csv", "officer"),
    ("gang.csv", "gang"),
    ("fir.csv", "fir"),
    ("victim.csv", "victim"),
    ("accused.csv", "accused"),
    ("evidence.csv", "evidence"),
    ("witness.csv", "witness"),
    ("court_case.csv", "court_case"),
    ("vehicle.csv", "vehicle"),
    ("cctv.csv", "cctv"),
    ("bond.csv", "bond"),
    ("history_sheet.csv", "history_sheet"),
    ("criminal_network.csv", "criminal_network"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bulk load generated KSP CSV files into Zoho Catalyst Data Store."
    )
    parser.add_argument(
        "--csv-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory containing generated CSV files.",
    )
    parser.add_argument(
        "--filestore-folder-id",
        required=True,
        help="Catalyst File Store folder ID used to upload CSV files before bulk write.",
    )
    parser.add_argument(
        "--operation",
        default="insert",
        choices=["insert", "update", "upsert"],
        help="Catalyst bulk write operation.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between Catalyst bulk job status polls.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Max seconds to wait for each bulk job.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional subset of Catalyst table names to load.",
    )
    parser.add_argument(
        "--project-id",
        default=os.getenv("CATALYST_PROJECT_ID"),
        help="Catalyst project ID. Defaults to CATALYST_PROJECT_ID.",
    )
    parser.add_argument(
        "--project-key",
        default=os.getenv("CATALYST_PROJECT_KEY"),
        help="Catalyst project key. Defaults to CATALYST_PROJECT_KEY.",
    )
    parser.add_argument(
        "--project-domain",
        default=os.getenv("CATALYST_PROJECT_DOMAIN"),
        help="Catalyst project domain, for example https://<project>.zohocatalyst.com.",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("CATALYST_ENVIRONMENT", "Development"),
        help="Catalyst environment name.",
    )
    return parser.parse_args()


def build_app(args):
    missing = [
        name
        for name, value in (
            ("project_id", args.project_id),
            ("project_key", args.project_key),
            ("project_domain", args.project_domain),
        )
        if not value
    ]
    if "CATALYST_AUTH" not in os.environ:
        raise RuntimeError("Missing CATALYST_AUTH environment variable with Catalyst credential JSON.")
    if missing:
        raise RuntimeError(f"Missing required Catalyst options: {', '.join(missing)}")

    options = {
        "project_id": args.project_id,
        "project_key": args.project_key,
        "project_domain": args.project_domain,
        "environment": args.environment,
    }
    return initialize_app(options=options)


def discover_tables(app):
    tables = app.datastore().get_all_tables()
    by_name = {}
    for table in tables:
        details = table.to_dict()
        name = details.get("table_name")
        if name:
            by_name[name] = table
    return by_name


def ensure_csv(path):
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")
    if csv_path.stat().st_size == 0:
        raise RuntimeError(f"CSV file is empty: {csv_path}")
    return csv_path


def select_load_plan(only):
    if not only:
        return LOAD_ORDER
    allowed = set(only)
    selected = [item for item in LOAD_ORDER if item[1] in allowed]
    missing = sorted(allowed - {table_name for _, table_name in selected})
    if missing:
        raise RuntimeError(f"Unknown table names in --only: {', '.join(missing)}")
    return selected


def wait_for_job(bulk_write, job_id, timeout_seconds, poll_interval):
    start = time.time()
    while True:
        status = bulk_write.get_status(job_id)
        status_text = str(
            status.get("status")
            or status.get("job_status")
            or status.get("operation_status")
            or ""
        ).lower()
        if status_text in {"completed", "success", "completed_successfully"}:
            return status
        if status_text in {"failed", "error", "aborted"}:
            raise RuntimeError(f"Bulk job {job_id} failed: {json.dumps(status, indent=2)}")
        if time.time() - start > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for bulk job {job_id}: {json.dumps(status, indent=2)}")
        time.sleep(poll_interval)


def upload_and_load(folder, table, csv_path, operation, timeout_seconds, poll_interval):
    with open(csv_path, "rb") as handle:
        uploaded = folder.upload_file(csv_path.name, handle)
    file_id = uploaded.get("id") or uploaded.get("file_id")
    if not file_id:
        raise RuntimeError(f"Could not determine uploaded file ID for {csv_path.name}: {uploaded}")

    job = table.bulk_write().create_job(file_id, options={"operation": operation})
    job_id = job.get("job_id") or job.get("id")
    if not job_id:
        raise RuntimeError(f"Could not determine bulk job ID for {csv_path.name}: {job}")

    final_status = wait_for_job(table.bulk_write(), job_id, timeout_seconds, poll_interval)
    return uploaded, job, final_status


def main():
    args = parse_args()
    app = build_app(args)
    csv_dir = Path(args.csv_dir).resolve()
    filestore_folder = app.filestore().folder(args.filestore_folder_id)
    table_map = discover_tables(app)
    plan = select_load_plan(args.only)
    results = []

    for filename, table_name in plan:
        if table_name not in table_map:
            raise RuntimeError(
                f"Catalyst Data Store table '{table_name}' was not found. "
                "Create the table and matching columns before loading."
            )

        csv_path = ensure_csv(csv_dir / filename)
        table = table_map[table_name]
        uploaded, job, final_status = upload_and_load(
            filestore_folder,
            table,
            csv_path,
            args.operation,
            args.timeout,
            args.poll_interval,
        )
        results.append(
            {
                "table": table_name,
                "csv_file": filename,
                "uploaded_file_id": uploaded.get("id") or uploaded.get("file_id"),
                "bulk_job_id": job.get("job_id") or job.get("id"),
                "status": final_status.get("status") or final_status.get("job_status") or "unknown",
            }
        )
        print(f"Loaded {filename} into Catalyst table '{table_name}'")

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

