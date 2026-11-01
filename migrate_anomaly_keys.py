
import hashlib
import json
import os

from database import get_connection


def stable_key(record):
    canonical = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def migrate():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Read existing records before making any changes.
            cur.execute("""
                SELECT id, raw_data
                FROM logs
                ORDER BY id
            """)
            rows = cur.fetchall()

            keys = []
            for log_id, raw_data in rows:
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)

                if not isinstance(raw_data, dict):
                    raise ValueError(
                        f"Log {log_id} has unexpected raw_data format."
                    )

                keys.append((stable_key(raw_data), log_id))

            if len({key for key, _ in keys}) != len(keys):
                raise ValueError(
                    "Duplicate raw_data records found. "
                    "No keys were changed."
                )

            # Ensure no pre-existing key conflicts.
            cur.execute("""
                SELECT COUNT(*)
                FROM logs
                WHERE source_key IS NOT NULL
            """)
            existing_keys = cur.fetchone()[0]

            if existing_keys:
                raise ValueError(
                    "Some source keys already exist. "
                    "Inspect the database before migrating."
                )

            # Assign a stable key to each existing log.
            for key, log_id in keys:
                cur.execute(
                    "UPDATE logs SET source_key = %s WHERE id = %s",
                    (key, log_id),
                )

            # Protect the keys against duplicate future imports.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_logs_source_key_unique
                ON logs (source_key)
                WHERE source_key IS NOT NULL
            """)

        # The transaction commits when the connection context exits.

    print(f"Keys assigned: {len(keys)}")
    print("Unique index created successfully.")


if __name__ == "__main__":
    if "DB_PASSWORD" not in os.environ:
        from getpass import getpass
        os.environ["DB_PASSWORD"] = getpass(
            "Enter PostgreSQL password: "
        )

    migrate()
