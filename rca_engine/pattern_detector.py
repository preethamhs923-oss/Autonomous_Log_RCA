import json
from datetime import datetime


# ============================================================
# LOAD LOGS
# ============================================================

def load_logs(file_path):
    """Load Member 2 anomaly results."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# TIMESTAMP
# ============================================================

def parse_timestamp(timestamp):
    """Convert timestamp string into datetime."""

    return datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# MESSAGE KEYWORD MATCHING
# ============================================================

def message_contains(message, keywords):
    """Check whether message contains any keyword."""

    message = message.lower()

    for keyword in keywords:

        if keyword.lower() in message:
            return True

    return False


# ============================================================
# DETECT SINGLE LOG PATTERN
# ============================================================

def detect_log_pattern(log):
    """
    Detect the likely technical category
    represented by a single log.
    """

    message = log.get("message", "").lower()
    level = log.get("level", "").upper()

    # --------------------------------------------------------
    # DATABASE FAILURE
    # --------------------------------------------------------

    database_keywords = [
        "database",
        "db error",
        "connection pool",
        "connection timeout",
        "database timeout",
        "sql error",
        "database connection"
    ]

    if message_contains(message, database_keywords):

        return "DATABASE_FAILURE"

    # --------------------------------------------------------
    # AUTHENTICATION FAILURE
    # --------------------------------------------------------

    authentication_keywords = [
        "failed login",
        "authentication failed",
        "unauthorized",
        "invalid password",
        "login failed",
        "access denied"
    ]

    if message_contains(message, authentication_keywords):

        return "AUTHENTICATION_FAILURE"

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    timeout_keywords = [
        "timeout",
        "timed out",
        "request timeout",
        "connection timeout"
    ]

    if message_contains(message, timeout_keywords):

        return "TIMEOUT_FAILURE"

    # --------------------------------------------------------
    # SERVICE FAILURE
    # --------------------------------------------------------

    service_keywords = [
        "service unavailable",
        "service failed",
        "internal server error",
        "server error",
        "service down"
    ]

    if message_contains(message, service_keywords):

        return "SERVICE_FAILURE"

    # --------------------------------------------------------
    # API FAILURE
    # --------------------------------------------------------

    api_keywords = [
        "api error",
        "api failure",
        "bad gateway",
        "gateway error",
        "request failed"
    ]

    if message_contains(message, api_keywords):

        return "API_FAILURE"

    # --------------------------------------------------------
    # RESOURCE / OVERLOAD
    # --------------------------------------------------------

    resource_keywords = [
        "high traffic",
        "too many requests",
        "rate limit",
        "resource exhausted",
        "memory",
        "cpu",
        "overload"
    ]

    if message_contains(message, resource_keywords):

        return "RESOURCE_OVERLOAD"

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    security_keywords = [
        "suspicious",
        "attack",
        "blocked",
        "malicious",
        "intrusion"
    ]

    if message_contains(message, security_keywords):

        return "SECURITY_EVENT"

    # --------------------------------------------------------
    # WARNING
    # --------------------------------------------------------

    if level == "WARNING":

        return "WARNING_EVENT"

    # --------------------------------------------------------
    # GENERAL ERROR
    # --------------------------------------------------------

    if level in ["ERROR", "CRITICAL"]:

        return "GENERAL_ERROR"

    return "NORMAL_EVENT"


# ============================================================
# DETECT INCIDENT PATTERN
# ============================================================

def detect_incident_pattern(logs):
    """
    Analyze a group of logs and identify
    the dominant failure pattern.
    """

    pattern_counts = {}

    for log in logs:

        pattern = detect_log_pattern(log)

        pattern_counts[pattern] = (
            pattern_counts.get(pattern, 0) + 1
        )

    # Remove normal events from root pattern calculation

    failure_patterns = {
        key: value
        for key, value in pattern_counts.items()
        if key != "NORMAL_EVENT"
    }

    if not failure_patterns:

        return {
            "pattern": "NO_FAILURE_PATTERN",
            "confidence": 0.0,
            "pattern_counts": pattern_counts
        }

    dominant_pattern = max(
        failure_patterns,
        key=failure_patterns.get
    )

    total_failure_events = sum(
        failure_patterns.values()
    )

    dominant_count = failure_patterns[
        dominant_pattern
    ]

    confidence = (
        dominant_count / total_failure_events
    )

    return {
        "pattern": dominant_pattern,
        "confidence": round(confidence, 3),
        "pattern_counts": pattern_counts
    }


# ============================================================
# BUILD INCIDENT WINDOWS
# ============================================================

def build_incident_windows(
    anomalies,
    window_seconds=120
):
    """
    Group anomalies occurring close together
    into potential incidents.
    """

    if not anomalies:

        return []

    sorted_anomalies = sorted(
        anomalies,
        key=lambda x: x.get("timestamp", "")
    )

    incidents = []

    current_incident = [
        sorted_anomalies[0]
    ]

    for log in sorted_anomalies[1:]:

        previous = current_incident[-1]

        try:

            current_time = parse_timestamp(
                log["timestamp"]
            )

            previous_time = parse_timestamp(
                previous["timestamp"]
            )

            difference = (
                current_time - previous_time
            ).total_seconds()

        except (ValueError, TypeError, KeyError):

            difference = window_seconds + 1

        if difference <= window_seconds:

            current_incident.append(log)

        else:

            incidents.append(current_incident)

            current_incident = [log]

    incidents.append(current_incident)

    return incidents


# ============================================================
# ANALYZE INCIDENTS
# ============================================================

def analyze_incidents(anomalies):

    incidents = build_incident_windows(
        anomalies
    )

    results = []

    for index, incident_logs in enumerate(
        incidents,
        start=1
    ):

        pattern_result = detect_incident_pattern(
            incident_logs
        )

        services = sorted(
            list(
                set(
                    log.get("service")
                    for log in incident_logs
                    if log.get("service")
                )
            )
        )

        severities = sorted(
            list(
                set(
                    log.get("severity")
                    for log in incident_logs
                    if log.get("severity")
                )
            )
        )

        results.append(
            {
                "incident_id": f"INC-{index:04d}",

                "start_time":
                    incident_logs[0].get("timestamp"),

                "end_time":
                    incident_logs[-1].get("timestamp"),

                "event_count":
                    len(incident_logs),

                "services":
                    services,

                "severities":
                    severities,

                "detected_pattern":
                    pattern_result["pattern"],

                "pattern_confidence":
                    pattern_result["confidence"],

                "pattern_counts":
                    pattern_result["pattern_counts"],

                "events":
                    incident_logs
            }
        )

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    input_file = (
        "ai_detection/output/anomaly_results.json"
    )

    output_file = (
        "rca_engine/pattern_results.json"
    )

    logs = load_logs(input_file)

    # Only anomalous events
    anomalies = [
        log
        for log in logs
        if log.get("final_status") == "ANOMALY"
    ]

    print("==============================================")
    print("       MEMBER 3 - PATTERN DETECTION")
    print("==============================================")

    print("Total logs      :", len(logs))
    print("Total anomalies :", len(anomalies))

    # Analyze incidents
    incidents = analyze_incidents(
        anomalies
    )

    print(
        "Potential incidents:",
        len(incidents)
    )

    print("\nDETECTED INCIDENT PATTERNS")
    print("----------------------------------------------")

    # Show first 10 incidents
    for incident in incidents[:10]:

        print(
            incident["incident_id"],
            "|",
            incident["start_time"],
            "→",
            incident["end_time"]
        )

        print(
            "Pattern    :",
            incident["detected_pattern"]
        )

        print(
            "Confidence :",
            incident["pattern_confidence"]
        )

        print(
            "Events     :",
            incident["event_count"]
        )

        print(
            "Services   :",
            ", ".join(
                incident["services"]
            )
        )

        print("----------------------------------------------")

    # Save results
    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            incidents,
            file,
            indent=4
        )

    print(
        "\nPattern results saved to:",
        output_file
    )