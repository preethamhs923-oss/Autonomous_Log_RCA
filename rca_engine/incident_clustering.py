import json
from datetime import datetime


# ============================================================
# LOAD DATA
# ============================================================

def load_logs(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# TIMESTAMP
# ============================================================

def parse_timestamp(timestamp):

    return datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# GET PATTERN
# ============================================================

def get_pattern(log):

    message = log.get(
        "message",
        ""
    ).lower()

    if any(
        keyword in message
        for keyword in [
            "database",
            "connection pool",
            "database connection",
            "sql error"
        ]
    ):

        return "DATABASE_FAILURE"

    if any(
        keyword in message
        for keyword in [
            "failed login",
            "authentication failed",
            "unauthorized",
            "invalid password"
        ]
    ):

        return "AUTHENTICATION_FAILURE"

    if any(
        keyword in message
        for keyword in [
            "timeout",
            "timed out"
        ]
    ):

        return "TIMEOUT_FAILURE"

    if any(
        keyword in message
        for keyword in [
            "service unavailable",
            "internal server error",
            "server error"
        ]
    ):

        return "SERVICE_FAILURE"

    if any(
        keyword in message
        for keyword in [
            "api error",
            "gateway error",
            "bad gateway",
            "request failed"
        ]
    ):

        return "API_FAILURE"

    return "GENERAL_ERROR"


# ============================================================
# CHECK WHETHER TWO EVENTS BELONG TO SAME INCIDENT
# ============================================================

def are_related(current, previous):

    try:

        current_time = parse_timestamp(
            current["timestamp"]
        )

        previous_time = parse_timestamp(
            previous["timestamp"]
        )

    except (ValueError, TypeError, KeyError):

        return False

    time_difference = abs(
        (
            current_time -
            previous_time
        ).total_seconds()
    )

    # Too far apart
    if time_difference > 120:

        return False

    # --------------------------------------------------------
    # SAME TRACE
    # --------------------------------------------------------

    if (
        current.get("trace_id")
        and
        current.get("trace_id")
        ==
        previous.get("trace_id")
    ):

        return True

    # --------------------------------------------------------
    # SAME SOURCE IP + CLOSE TIME
    # --------------------------------------------------------

    if (
        current.get("source_ip")
        and
        current.get("source_ip")
        ==
        previous.get("source_ip")
        and
        time_difference <= 60
    ):

        return True

    # --------------------------------------------------------
    # SAME SERVICE + CLOSE TIME
    # --------------------------------------------------------

    if (
        current.get("service")
        and
        current.get("service")
        ==
        previous.get("service")
        and
        time_difference <= 30
    ):

        return True

    # --------------------------------------------------------
    # COMPATIBLE FAILURE PATTERN + CLOSE TIME
    # --------------------------------------------------------

    current_pattern = get_pattern(
        current
    )

    previous_pattern = get_pattern(
        previous
    )

    if (
        current_pattern ==
        previous_pattern
        and
        time_difference <= 30
    ):

        return True

    return False


# ============================================================
# CLUSTER INCIDENTS
# ============================================================

def cluster_incidents(anomalies):

    if not anomalies:

        return []

    anomalies = sorted(
        anomalies,
        key=lambda x: x.get(
            "timestamp",
            ""
        )
    )

    incidents = []

    current_incident = [
        anomalies[0]
    ]

    for current in anomalies[1:]:

        previous = current_incident[-1]

        if are_related(
            current,
            previous
        ):

            current_incident.append(
                current
            )

        else:

            incidents.append(
                current_incident
            )

            current_incident = [
                current
            ]

    incidents.append(
        current_incident
    )

    return incidents


# ============================================================
# BUILD INCIDENT INFORMATION
# ============================================================

def build_incident_results(
    incidents
):

    results = []

    for index, events in enumerate(
        incidents,
        start=1
    ):

        patterns = {}

        services = set()

        severities = set()

        for event in events:

            pattern = get_pattern(
                event
            )

            patterns[pattern] = (
                patterns.get(
                    pattern,
                    0
                ) + 1
            )

            if event.get(
                "service"
            ):

                services.add(
                    event["service"]
                )

            if event.get(
                "severity"
            ):

                severities.add(
                    event["severity"]
                )

        dominant_pattern = max(
            patterns,
            key=patterns.get
        )

        result = {

            "incident_id":
                f"INC-{index:04d}",

            "start_time":
                events[0].get(
                    "timestamp"
                ),

            "end_time":
                events[-1].get(
                    "timestamp"
                ),

            "event_count":
                len(events),

            "services":
                sorted(
                    services
                ),

            "severities":
                sorted(
                    severities
                ),

            "dominant_pattern":
                dominant_pattern,

            "pattern_counts":
                patterns,

            "events":
                events
        }

        results.append(
            result
        )

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    input_file = (
        "ai_detection/output/"
        "anomaly_results.json"
    )

    output_file = (
        "rca_engine/"
        "incident_results.json"
    )

    logs = load_logs(
        input_file
    )

    anomalies = [
        log
        for log in logs
        if log.get(
            "final_status"
        ) == "ANOMALY"
    ]

    print(
        "=============================================="
    )

    print(
        "       MEMBER 3 - INCIDENT CLUSTERING"
    )

    print(
        "=============================================="
    )

    print(
        "Total logs      :",
        len(logs)
    )

    print(
        "Total anomalies :",
        len(anomalies)
    )

    incidents = cluster_incidents(
        anomalies
    )

    results = build_incident_results(
        incidents
    )

    print(
        "Detected incidents:",
        len(results)
    )

    print(
        "\nINCIDENT SUMMARY"
    )

    print(
        "----------------------------------------------"
    )

    for incident in results[:20]:

        print(
            incident["incident_id"],
            "|",
            incident["start_time"],
            "→",
            incident["end_time"]
        )

        print(
            "Events  :",
            incident["event_count"]
        )

        print(
            "Pattern :",
            incident["dominant_pattern"]
        )

        print(
            "Services:",
            ", ".join(
                incident["services"]
            )
        )

        print(
            "----------------------------------------------"
        )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    print(
        "\nIncident results saved to:",
        output_file
    )