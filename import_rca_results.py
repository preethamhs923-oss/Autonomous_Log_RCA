
import hashlib
import json
from pathlib import Path

from database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parent

RESULT_FILES = {
    "incidents": PROJECT_ROOT / "rca_engine" / "incident_results.json",
    "incident_intelligence": (
        PROJECT_ROOT / "rca_engine" / "incident_intelligence_results.json"
    ),
    "root_causes": PROJECT_ROOT / "rca_engine" / "root_cause_results.json",
    "code_intelligence": (
        PROJECT_ROOT / "code_intelligence" / "output"
        / "code_intelligence_report.json"
    ),
    "refactoring": (
        PROJECT_ROOT / "code_intelligence" / "output"
        / "refactoring_recommendations.json"
    ),
}


def load_json(path):
    """Load a required JSON result file."""
    if not path.exists():
        raise FileNotFoundError(f"Required result file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def stable_key(record):
    """Generate the same deterministic key used for imported log records."""
    canonical_json = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def as_confidence(value):
    """Convert confidence to a number, or None if unavailable."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def import_results():
    # 1. Load and validate the JSON files.
    data = {
        name: load_json(path)
        for name, path in RESULT_FILES.items()
    }

    for name in ("incidents", "incident_intelligence", "root_causes"):
        if not isinstance(data[name], list):
            raise ValueError(f"{name} JSON must contain a list.")

    for name in ("code_intelligence", "refactoring"):
        if not isinstance(data[name], dict):
            raise ValueError(f"{name} JSON must contain an object.")

    intelligence_by_id = {
        str(item["incident_id"]): item
        for item in data["incident_intelligence"]
        if isinstance(item, dict) and item.get("incident_id") is not None
    }

    incident_count = 0
    event_count = 0
    unmatched_events = 0
    root_cause_count = 0
    report_count = 0
    recommendation_count = 0

    with get_connection() as conn:
        with conn.cursor() as cur:

            # 2. Import incidents and enrich them with incident intelligence.
            incident_db_ids = {}

            for item in data["incidents"]:
                if not isinstance(item, dict):
                    continue

                source_id = item.get("incident_id")
                if source_id is None:
                    continue

                source_id = str(source_id)
                intel = intelligence_by_id.get(source_id, {})

                title = (
                    intel.get("root_cause_message")
                    or item.get("dominant_pattern")
                    or f"Incident {source_id}"
                )

                severities = item.get("severities") or []
                severity = (
                    intel.get("severity")
                    or (
                        severities[0]
                        if isinstance(severities, list) and severities
                        else None
                    )
                )

                cur.execute(
                    """
                    INSERT INTO incidents (
                        incident_key,
                        title,
                        status,
                        severity,
                        first_seen,
                        last_seen,
                        incident_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (incident_key)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        severity = EXCLUDED.severity,
                        first_seen = EXCLUDED.first_seen,
                        last_seen = EXCLUDED.last_seen,
                        incident_data = EXCLUDED.incident_data
                    RETURNING id
                    """,
                    (
                        source_id,
                        title,
                        "open",
                        severity,
                        item.get("start_time"),
                        item.get("end_time"),
                        json.dumps({
                            "incident": item,
                            "intelligence": intel,
                        }),
                    ),
                )

                incident_db_ids[source_id] = cur.fetchone()[0]
                incident_count += 1

            # 3. Import events for each incident.
            # Rebuild this relationship table from the current JSON results,
            # preventing duplicate event mappings on repeated imports.
            cur.execute("DELETE FROM incident_events")

            for item in data["incidents"]:
                if not isinstance(item, dict):
                    continue

                source_id = item.get("incident_id")
                if source_id is None:
                    continue

                db_incident_id = incident_db_ids.get(str(source_id))
                if db_incident_id is None:
                    continue

                events = item.get("events", [])
                if not isinstance(events, list):
                    continue

                for event in events:
                    if not isinstance(event, dict):
                        continue

                    # Match this event to its already imported log.
                    event_key = stable_key(event)

                    cur.execute(
                        """
                        SELECT id
                        FROM logs
                        WHERE source_key = %s
                        ORDER BY id
                        LIMIT 1
                        """,
                        (event_key,),
                    )
                    log_row = cur.fetchone()

                    # Fallback: match the complete JSON record.
                    if log_row is None:
                        cur.execute(
                            """
                            SELECT id
                            FROM logs
                            WHERE raw_data = %s::jsonb
                            ORDER BY id
                            LIMIT 1
                            """,
                            (json.dumps(event),),
                        )
                        log_row = cur.fetchone()

                    if log_row is None:
                        unmatched_events += 1
                        continue

                    log_id = log_row[0]

                    # Link the anomaly when one exists for this log.
                    cur.execute(
                        """
                        SELECT id
                        FROM anomalies
                        WHERE log_id = %s
                        ORDER BY id
                        LIMIT 1
                        """,
                        (log_id,),
                    )
                    anomaly_row = cur.fetchone()
                    anomaly_id = anomaly_row[0] if anomaly_row else None

                    cur.execute(
                        """
                        INSERT INTO incident_events (
                            incident_id,
                            log_id,
                            anomaly_id,
                            event_data
                        )
                        VALUES (%s, %s, %s, %s::jsonb)
                        """,
                        (
                            db_incident_id,
                            log_id,
                            anomaly_id,
                            json.dumps(event),
                        ),
                    )

                    event_count += 1

            # 4. Import root-cause results, updating existing rows.
            for item in data["root_causes"]:
                if not isinstance(item, dict):
                    continue

                source_id = item.get("incident_id")
                if source_id is None:
                    continue

                source_id = str(source_id)
                db_incident_id = incident_db_ids.get(source_id)

                if db_incident_id is None:
                    cur.execute(
                        """
                        SELECT id
                        FROM incidents
                        WHERE incident_key = %s
                        """,
                        (source_id,),
                    )
                    row = cur.fetchone()

                    if row is None:
                        print(f"WARNING: Incident not found: {source_id}")
                        continue

                    db_incident_id = row[0]

                intel = intelligence_by_id.get(source_id, {})

                root_cause = (
                    intel.get("root_cause")
                    or item.get("root_cause")
                )

                confidence = as_confidence(
                    intel.get("confidence", item.get("confidence"))
                )

                explanation = (
                    intel.get("root_cause_message")
                    or item.get("root_cause_message")
                    or intel.get("summary")
                )

                result_data = {
                    "root_cause_result": item,
                    "incident_intelligence": intel,
                }

                cur.execute(
                    """
                    SELECT id
                    FROM root_cause_results
                    WHERE incident_id = %s
                    ORDER BY id
                    LIMIT 1
                    """,
                    (db_incident_id,),
                )
                existing = cur.fetchone()

                if existing:
                    cur.execute(
                        """
                        UPDATE root_cause_results
                        SET root_cause = %s,
                            confidence = %s,
                            explanation = %s,
                            result_data = %s::jsonb
                        WHERE id = %s
                        """,
                        (
                            root_cause,
                            confidence,
                            explanation,
                            json.dumps(result_data),
                            existing[0],
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO root_cause_results (
                            incident_id,
                            root_cause,
                            confidence,
                            explanation,
                            result_data
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb)
                        """,
                        (
                            db_incident_id,
                            root_cause,
                            confidence,
                            explanation,
                            json.dumps(result_data),
                        ),
                    )

                root_cause_count += 1

            # 5. Keep one current Code Intelligence report.
            cur.execute(
                """
                DELETE FROM code_analysis_results
                WHERE analysis_type = %s
                """,
                ("code_intelligence_report",),
            )

            cur.execute(
                """
                INSERT INTO code_analysis_results (
                    analysis_type,
                    target_file,
                    result_data
                )
                VALUES (%s, %s, %s::jsonb)
                """,
                (
                    "code_intelligence_report",
                    None,
                    json.dumps(data["code_intelligence"]),
                ),
            )
            report_count = 1

            # 6. Replace the imported refactoring recommendations.
            cur.execute("DELETE FROM refactoring_recommendations")

            recommendations = data["refactoring"].get(
                "recommendations", []
            )

            if not isinstance(recommendations, list):
                raise ValueError(
                    "The recommendations field must contain a list."
                )

            for item in recommendations:
                if not isinstance(item, dict):
                    continue

                target_file = item.get("target_file") or item.get("file")

                recommendation = (
                    item.get("recommendation")
                    or item.get("description")
                    or str(item)
                )

                cur.execute(
                    """
                    INSERT INTO refactoring_recommendations (
                        target_file,
                        recommendation,
                        priority,
                        result_data
                    )
                    VALUES (%s, %s, %s, %s::jsonb)
                    """,
                    (
                        target_file,
                        str(recommendation),
                        item.get("priority"),
                        json.dumps(item),
                    ),
                )

                recommendation_count += 1

        # Successful exit commits the transaction.
        # Exceptions roll back the transaction.

    print("\n=== RCA DATABASE IMPORT SUMMARY ===")
    print(f"Incidents processed: {incident_count}")
    print(f"Incident events imported: {event_count}")
    print(f"Events without a matching log: {unmatched_events}")
    print(f"Root-cause records processed: {root_cause_count}")
    print(f"Code Intelligence reports imported: {report_count}")
    print(f"Refactoring recommendations imported: {recommendation_count}")
    print("Import transaction completed successfully.")


if __name__ == "__main__":
    import_results()
