from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path


app = Flask(__name__)
CORS(app)


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Existing anomaly detection output
ANOMALY_FILE = (
    BASE_DIR
    / "ai_detection"
    / "output"
    / "anomaly_results.json"
)


def load_anomaly_data():

    if not ANOMALY_FILE.exists():
        return []

    with open(ANOMALY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


@app.route("/api/health")
def health():

    return jsonify({
        "status": "online",
        "service": "Autonomous Log RCA API"
    })


@app.route("/api/dashboard")
def dashboard():

    data = load_anomaly_data()

    total_logs = len(data)

    anomalies = [
        item for item in data
        if item.get("status") == "ANOMALY"
    ]

    critical = [
        item for item in data
        if item.get("severity") == "CRITICAL"
    ]

    high = [
        item for item in data
        if item.get("severity") == "HIGH"
    ]

    medium = [
        item for item in data
        if item.get("severity") == "MEDIUM"
    ]

    low = [
        item for item in data
        if item.get("severity") == "LOW"
    ]

    services = {}

    for item in data:

        service = item.get("service", "unknown")

        if service not in services:
            services[service] = {
                "total": 0,
                "anomalies": 0
            }

        services[service]["total"] += 1

        if item.get("status") == "ANOMALY":
            services[service]["anomalies"] += 1

    return jsonify({

        "summary": {
            "total_logs": total_logs,
            "anomalies": len(anomalies),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low)
        },

        "services": services,

        "recent_anomalies": anomalies[-20:],

        "all_logs": data
    })


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )