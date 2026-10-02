import json
import os
from collections import Counter


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_CAUSE_FILE = os.path.join(
    BASE_DIR,
    "root_cause_results.json"
)

INCIDENT_FILE = os.path.join(
    BASE_DIR,
    "incident_results.json"
)

PATTERN_FILE = os.path.join(
    BASE_DIR,
    "pattern_results.json"
)

ANOMALY_FILE = os.path.join(
    BASE_DIR,
    "..",
    "ai_detection",
    "output",
    "anomaly_results.json"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "incident_intelligence_results.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(file_path):

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# LOAD ALL PROJECT DATA
# ============================================================

root_causes = load_json(ROOT_CAUSE_FILE)
incidents = load_json(INCIDENT_FILE)
patterns = load_json(PATTERN_FILE)
anomalies = load_json(ANOMALY_FILE)


# ============================================================
# CREATE LOOKUP FOR ANOMALIES
# ============================================================

anomaly_lookup = {}

for anomaly in anomalies:

    trace_id = anomaly.get("trace_id")

    if trace_id:
        anomaly_lookup[trace_id] = anomaly


# ============================================================
# FIND ANOMALY INFORMATION FOR INCIDENT
# ============================================================

def get_incident_anomalies(incident):

    events = incident.get("events", [])

    matched = []

    for event in events:

        trace_id = event.get("trace_id")

        if trace_id and trace_id in anomaly_lookup:
            matched.append(anomaly_lookup[trace_id])

    return matched


# ============================================================
# GENERATE INCIDENT SEVERITY
# ============================================================

def calculate_severity(incident, root_cause, anomaly_events):

    severities = []

    for event in anomaly_events:

        severity = event.get("severity")

        if severity:
            severities.append(severity.upper())

    if "CRITICAL" in severities:
        return "CRITICAL"

    if "HIGH" in severities:
        return "HIGH"

    if "MEDIUM" in severities:
        return "MEDIUM"

    root_confidence = root_cause.get("confidence", 0)

    if root_confidence >= 0.75:
        return "HIGH"

    if root_confidence >= 0.50:
        return "MEDIUM"

    return "LOW"


# ============================================================
# GENERATE INCIDENT SUMMARY
# ============================================================

def generate_summary(
    incident,
    root_cause,
    severity
):

    pattern = incident.get(
        "dominant_pattern",
        root_cause.get("root_cause", "UNKNOWN")
    )

    services = incident.get(
        "services",
        []
    )

    event_count = incident.get(
        "event_count",
        0
    )

    root_cause_name = root_cause.get(
        "root_cause",
        "UNKNOWN"
    )

    root_message = root_cause.get(
        "root_cause_message",
        ""
    )

    if not root_message:
        root_message = root_cause.get(
            "message",
            ""
        )

    if root_cause_name == "DATABASE_FAILURE":

        return (
            f"{severity} incident detected involving "
            f"database-related failures. "
            f"{event_count} related events were identified "
            f"across {len(services)} services. "
            f"Root cause analysis indicates "
            f"{root_cause_name.lower().replace('_', ' ')}."
        )

    if root_cause_name == "AUTHENTICATION_FAILURE":

        return (
            f"{severity} authentication-related incident detected. "
            f"{event_count} related events were identified "
            f"across {len(services)} services. "
            f"Root cause analysis indicates "
            f"{root_cause_name.lower().replace('_', ' ')}."
        )

    if root_cause_name == "SERVICE_FAILURE":

        return (
            f"{severity} service failure detected. "
            f"{event_count} related events were identified "
            f"across {len(services)} services."
        )

    return (
        f"{severity} incident detected with pattern "
        f"{pattern}. "
        f"{event_count} related events were identified "
        f"across {len(services)} services."
    )


# ============================================================
# GENERATE RECOMMENDED ACTION
# ============================================================

def generate_recommendation(root_cause):

    root_cause_name = root_cause.get(
        "root_cause",
        "UNKNOWN"
    )

    if root_cause_name == "DATABASE_FAILURE":

        return (
            "Check database availability, connection pool "
            "capacity, database connectivity, and active "
            "database connections."
        )

    if root_cause_name == "AUTHENTICATION_FAILURE":

        return (
            "Check authentication services, credential "
            "validation, login failure frequency, and "
            "possible suspicious authentication activity."
        )

    if root_cause_name == "SERVICE_FAILURE":

        return (
            "Check service health, service availability, "
            "application errors, and dependent services."
        )

    if root_cause_name == "NETWORK_FAILURE":

        return (
            "Check network connectivity, service endpoints, "
            "latency, and network infrastructure."
        )

    return (
        "Investigate the correlated events and affected "
        "services for additional evidence."
    )


# ============================================================
# BUILD INCIDENT INTELLIGENCE
# ============================================================

def build_intelligence():

    results = []

    print("\n==============================================")
    print("       MEMBER 3 - INCIDENT INTELLIGENCE")
    print("==============================================")

    print(
        f"Root cause records : {len(root_causes)}"
    )

    print(
        f"Incident records   : {len(incidents)}"
    )

    print(
        f"Anomaly records    : {len(anomalies)}"
    )

    # --------------------------------------------------------
    # ROOT CAUSE RECORDS ARE USED AS THE PRIMARY INCIDENT
    # SOURCE
    # --------------------------------------------------------

    for root_cause in root_causes:

        incident_id = root_cause.get(
            "incident_id",
            "UNKNOWN"
        )

        # Find matching incident
        incident = None

        for item in incidents:

            if item.get("incident_id") == incident_id:
                incident = item
                break

        if incident is None:
            incident = {}

        anomaly_events = get_incident_anomalies(
            incident
        )

        severity = calculate_severity(
            incident,
            root_cause,
            anomaly_events
        )

        summary = generate_summary(
            incident,
            root_cause,
            severity
        )

        recommendation = generate_recommendation(
            root_cause
        )

        services = incident.get(
            "services",
            []
        )

        pattern = incident.get(
            "dominant_pattern",
            root_cause.get(
                "root_cause",
                "UNKNOWN"
            )
        )

        evidence = root_cause.get(
            "evidence",
            []
        )

        confidence = root_cause.get(
            "confidence",
            0
        )

        result = {

            "incident_id": incident_id,

            "start_time": incident.get(
                "start_time"
            ),

            "end_time": incident.get(
                "end_time"
            ),

            "event_count": incident.get(
                "event_count",
                0
            ),

            "services_affected": services,

            "pattern": pattern,

            "root_cause": root_cause.get(
                "root_cause",
                "UNKNOWN"
            ),

            "root_cause_message": root_cause.get(
                "root_cause_message",
                root_cause.get(
                    "message",
                    ""
                )
            ),

            "confidence": confidence,

            "severity": severity,

            "evidence": evidence,

            "summary": summary,

            "recommended_action": recommendation
        }

        results.append(result)

    return results


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    print(
        f"\nIncident intelligence saved to:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(results):

    print("\n==============================================")
    print("       INCIDENT INTELLIGENCE RESULTS")
    print("==============================================")

    print(
        f"Total incidents: {len(results)}"
    )

    print()

    for result in results[:10]:

        print("----------------------------------------------")

        print(
            "Incident ID       :",
            result.get("incident_id")
        )

        print(
            "Pattern           :",
            result.get("pattern")
        )

        print(
            "Root Cause        :",
            result.get("root_cause")
        )

        print(
            "Severity          :",
            result.get("severity")
        )

        print(
            "Confidence        :",
            result.get("confidence")
        )

        print(
            "Events            :",
            result.get("event_count")
        )

        print(
            "Services          :",
            ", ".join(
                result.get(
                    "services_affected",
                    []
                )
            )
        )

        print(
            "Summary           :",
            result.get("summary")
        )

        print(
            "Recommended Action:",
            result.get(
                "recommended_action"
            )
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    results = build_intelligence()

    save_results(results)

    display_results(results)