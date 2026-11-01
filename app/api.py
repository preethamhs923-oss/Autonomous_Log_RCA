
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import json
import sys

# Allow the app folder to import the project's database.py
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database import get_connection

app = Flask(__name__)
CORS(app)


def fetch_dashboard_data():
    """Read logs and anomaly results from PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Fetch logs and their stored raw data.
            cur.execute("""
                SELECT id, source_key, source, timestamp,
                       service_name, level, message, raw_data
                FROM logs
                ORDER BY id
            """)

            log_rows = cur.fetchall()

            # Fetch anomaly records and the associated log data.
            cur.execute("""
                SELECT
                    l.id,
                    l.source_key,
                    l.timestamp,
                    l.service_name,
                    l.level,
                    l.message,
                    l.raw_data,
                    a.anomaly_score,
                    a.severity,
                    a.detection_method,
                    a.description,
                    a.result_data
                FROM anomalies a
                JOIN logs l ON l.id = a.log_id
                ORDER BY a.id
            """)

            anomaly_rows = cur.fetchall()

    all_logs = []

    for row in log_rows:
        raw_data = row[7] or {}

        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except json.JSONDecodeError:
                raw_data = {}

        item = dict(raw_data) if isinstance(raw_data, dict) else {}

        item.setdefault("id", row[0])
        item.setdefault("source_key", row[1])
        item.setdefault("timestamp", row[3].isoformat() if row[3] else None)
        item.setdefault("service", row[4] or "unknown")
        item.setdefault("level", row[5])
        item.setdefault("message", row[6])

        all_logs.append(item)

    anomaly_records = []

    for row in anomaly_rows:
        result_data = row[11] or {}

        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except json.JSONDecodeError:
                result_data = {}

        item = dict(result_data) if isinstance(result_data, dict) else {}

        item.setdefault("id", row[0])
        item.setdefault("source_key", row[1])
        item.setdefault("timestamp", row[2].isoformat() if row[2] else None)
        item.setdefault("service", row[3] or "unknown")
        item.setdefault("level", row[4])
        item.setdefault("message", row[5])
        item.setdefault("anomaly_score", row[7])
        item.setdefault("severity", row[8])
        item.setdefault("detection_method", row[9])
        item.setdefault("explanation", row[10])

        # Normalize status for the existing frontend.
        status = item.get("final_status") or item.get("status")

        if not status:
            status = "ANOMALY" if row[7] is not None else "NORMAL"

        item["status"] = str(status).upper()
        anomaly_records.append(item)

    return all_logs, anomaly_records


@app.route("/api/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                database_name = cur.fetchone()[0]

        return jsonify({
            "status": "online",
            "service": "Autonomous Log RCA API",
            "database": "connected",
            "database_name": database_name
        })

    except Exception:
        app.logger.exception("Database health check failed")
        return jsonify({
            "status": "error",
            "service": "Autonomous Log RCA API",
            "database": "disconnected"
        }), 503


@app.route("/api/dashboard")
def dashboard():
    try:
        all_logs, data = fetch_dashboard_data()

        anomalies = [
            item for item in data
            if item.get("status") == "ANOMALY"
        ]

        critical = [
            item for item in anomalies
            if str(item.get("severity", "")).upper() == "CRITICAL"
        ]

        high = [
            item for item in anomalies
            if str(item.get("severity", "")).upper() == "HIGH"
        ]

        medium = [
            item for item in anomalies
            if str(item.get("severity", "")).upper() == "MEDIUM"
        ]

        low = [
            item for item in anomalies
            if str(item.get("severity", "")).upper() == "LOW"
        ]

        
        services = {}

        # Count total logs for each service.
        for item in all_logs:
            service = item.get("service", "unknown")

            if service not in services:
                services[service] = {
                    "total": 0,
                    "anomalies": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "status": "HEALTHY"
                }

            services[service]["total"] += 1

        # Count anomalies and their severity for each service.
        for item in anomalies:
            service = item.get("service", "unknown")
            severity = str(item.get("severity", "")).upper()

            if service not in services:
                services[service] = {
                    "total": 0,
                    "anomalies": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "status": "HEALTHY"
                }

            services[service]["anomalies"] += 1

            if severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                services[service][severity.lower()] += 1

        # Calculate service health from its anomaly severity.
        for service_data in services.values():

            if service_data["critical"] > 0:
                service_data["status"] = "CRITICAL"

            elif service_data["high"] > 0 or service_data["medium"] > 0:
                service_data["status"] = "DEGRADED"

            else:
                service_data["status"] = "HEALTHY"


        return jsonify({
            "summary": {
                "total_logs": len(all_logs),
                "anomalies": len(anomalies),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low)
            },
            "services": services,
            "recent_anomalies": anomalies[-20:],
            "all_logs": all_logs
        })

    except Exception:
        app.logger.exception("Dashboard database query failed")
        return jsonify({
            "error": "Unable to load dashboard data from PostgreSQL."
        }), 500


def fetch_table_rows(table_name):
    """Fetch records from a known project database table."""
    allowed_tables = {
        "incidents",
        "incident_events",
        "root_cause_results",
        "code_analysis_results",
        "refactoring_recommendations",
    }

    if table_name not in allowed_tables:
        raise ValueError("Table is not allowed")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name}")
            columns = [column[0] for column in cur.description]
            rows = cur.fetchall()

    # Convert dates, decimals, and other values into JSON-safe values.
    return json.loads(
        json.dumps(
            [dict(zip(columns, row)) for row in rows],
            default=str
        )
    )


def api_error(message):
    app.logger.exception(message)
    return jsonify({"error": message}), 500


@app.route("/api/logs")
def get_logs():
    try:
        logs, _ = fetch_dashboard_data()
        return jsonify({"count": len(logs), "logs": logs})
    except Exception:
        return api_error("Unable to fetch logs.")


@app.route("/api/anomalies")
def get_anomalies():
    try:
        _, anomalies = fetch_dashboard_data()
        anomalies = [
            item for item in anomalies
            if item.get("status") == "ANOMALY"
        ]
        return jsonify({
            "count": len(anomalies),
            "anomalies": anomalies
        })
    except Exception:
        return api_error("Unable to fetch anomalies.")


@app.route("/api/incidents")
def get_incidents():
    try:
        rows = fetch_table_rows("incidents")
        return jsonify({
            "count": len(rows),
            "incidents": rows
        })
    except Exception:
        return api_error("Unable to fetch incidents.")


@app.route("/api/incident-events")
def get_incident_events():
    try:
        rows = fetch_table_rows("incident_events")
        return jsonify({
            "count": len(rows),
            "events": rows
        })
    except Exception:
        return api_error("Unable to fetch incident events.")


@app.route("/api/root-causes")
def get_root_causes():
    try:
        rows = fetch_table_rows("root_cause_results")
        return jsonify({
            "count": len(rows),
            "root_causes": rows
        })
    except Exception:
        return api_error("Unable to fetch root-cause results.")


@app.route("/api/ai-intelligence")
def get_ai_intelligence():
    try:
        analyses = fetch_table_rows("code_analysis_results")
        recommendations = fetch_table_rows(
            "refactoring_recommendations"
        )

        return jsonify({
            "analysis_count": len(analyses),
            "recommendation_count": len(recommendations),
            "code_analysis": analyses,
            "refactoring_recommendations": recommendations
        })
    except Exception:
        return api_error("Unable to fetch AI Intelligence results.")


@app.route("/api/security")
def get_security():
    try:
        _, anomaly_records = fetch_dashboard_data()

        security_records = [
            item for item in anomaly_records
            if (
                str(item.get("severity", "")).upper()
                in ("CRITICAL", "HIGH")
                or item.get("rule_anomaly") is True
                or item.get("failed_login") is True
            )
        ]

        return jsonify({
            "count": len(security_records),
            "security_events": security_records
        })
    except Exception:
        return api_error("Unable to fetch security events.")


@app.route("/api/settings")
def get_settings():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                database_name = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM logs")
                total_logs = cur.fetchone()[0]

        return jsonify({
            "application": "Autonomous Log RCA",
            "backend": "Flask",
            "database": database_name,
            "database_status": "connected",
            "api_base_url": "http://127.0.0.1:5000/api",
            "total_logs": total_logs
        })
    except Exception:
        return api_error("Unable to fetch application settings.")

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
