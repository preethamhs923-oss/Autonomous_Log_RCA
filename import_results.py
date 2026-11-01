
import hashlib
import json
import os
from pathlib import Path

from database import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent
ANOMALY_FILE = (
    PROJECT_ROOT / "ai_detection" / "output" / "anomaly_results.json"
)


def stable_key(record):
    """Create a stable hash for a source JSON record."""
    canonical_json = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def import_anomalies():
    if not ANOMALY_FILE.exists():
        raise FileNotFoundError(f"File not found: {ANOMALY_FILE}")

    with ANOMALY_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected anomaly_results.json to contain a list.")

    inserted = 0
    skipped = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for record in records:
                if not isinstance(record, dict):
                    skipped += 1
                    continue

                key = stable_key(record)

                cur.execute(
                    """
                    INSERT INTO logs (
                        source_key, source, timestamp, service_name,
                        level, message, raw_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                      ON CONFLICT (source_key) WHERE source_key IS NOT NULL DO NOTHING
                      RETURNING id
                    """,
                    (
                        key,
                        record.get("source_ip"),
                        record.get("timestamp"),
                        record.get("service"),
                        record.get("level"),
                        record.get("message"),
                        json.dumps(record),
                    ),
                )

                row = cur.fetchone()

                if row is None:
               # The log already exists. Retrieve its existing ID.
                   cur.execute(
                     "SELECT id FROM logs WHERE source_key = %s",
                        (key,),
                    )
                   existing_log = cur.fetchone()

                   if existing_log is None:
                    skipped += 1
                    continue

                   log_id = existing_log[0]
                else:
                   log_id = row[0]
            if record.get("final_status") == "ANOMALY":
                
                cur.execute(
                    """
                    INSERT INTO anomalies (
                        log_id, anomaly_score, severity,
                        detection_method, description, result_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT ON CONSTRAINT anomalies_log_id_unique DO NOTHING
                    """,
                    (
                        log_id,
                        record.get("anomaly_score"),
                        record.get("severity"),
                        "combined",
                        record.get("explanation"),
                        json.dumps(record),
                    ),
                )

                inserted += 1

    print(f"New anomaly records imported: {inserted}")
    print(f"Records skipped: {skipped}")


if __name__ == "__main__":
    if "DB_PASSWORD" not in os.environ:
        from getpass import getpass
        os.environ["DB_PASSWORD"] = getpass("PostgreSQL password: ")

    import_anomalies()
