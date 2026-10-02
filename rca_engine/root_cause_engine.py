import json
from datetime import datetime


# ============================================================
# LOAD INCIDENTS
# ============================================================

def load_incidents(file_path):

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
# ROOT CAUSE CANDIDATE CLASSIFICATION
# ============================================================

def classify_candidate(event):

    message = event.get(
        "message",
        ""
    ).lower()

    pattern = event.get(
        "pattern",
        ""
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    database_keywords = [
        "database",
        "connection pool",
        "database connection",
        "sql",
        "query failed",
        "connection timeout"
    ]

    if any(
        keyword in message
        for keyword in database_keywords
    ):

        return "DATABASE_FAILURE"

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    authentication_keywords = [
    "failed login",
    "login failed",
    "authentication failed",
    "invalid credentials",
    "invalid password",
    "unauthorized",
    "access denied",
    "authentication error",
    "authentication failure"
]

    if any(
        keyword in message
        for keyword in authentication_keywords
    ):

        return "AUTHENTICATION_FAILURE"

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    timeout_keywords = [
        "timeout",
        "timed out"
    ]

    if any(
        keyword in message
        for keyword in timeout_keywords
    ):

        return "TIMEOUT_FAILURE"

    # --------------------------------------------------------
    # SERVICE
    # --------------------------------------------------------

    service_keywords = [
        "service unavailable",
        "service failed",
        "internal server error",
        "server error",
        "service down"
    ]

    if any(
        keyword in message
        for keyword in service_keywords
    ):

        return "SERVICE_FAILURE"

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    api_keywords = [
        "api error",
        "gateway error",
        "bad gateway",
        "request failed"
    ]

    if any(
        keyword in message
        for keyword in api_keywords
    ):

        return "API_FAILURE"

    # --------------------------------------------------------
    # RESOURCE
    # --------------------------------------------------------

    resource_keywords = [
        "resource exhausted",
        "too many requests",
        "high traffic",
        "overload",
        "memory",
        "cpu"
    ]

    if any(
        keyword in message
        for keyword in resource_keywords
    ):

        return "RESOURCE_OVERLOAD"

    # --------------------------------------------------------
    # FALLBACK TO INCIDENT PATTERN
    # --------------------------------------------------------

    if pattern:

        return pattern

    return "UNKNOWN"


# ============================================================
# SCORE A ROOT CAUSE CANDIDATE
# ============================================================

def score_candidate(
    event,
    incident_start,
    incident_end
):

    score = 0
    evidence = []

    # --------------------------------------------------------
    # 1. ANOMALY SCORE
    # --------------------------------------------------------

    anomaly_score = event.get(
        "anomaly_score",
        0
    )

    try:
        anomaly_score = float(
            anomaly_score
        )
    except (ValueError, TypeError):
        anomaly_score = 0

    if anomaly_score >= 0.60:

        score += 25

        evidence.append(
            "High anomaly score"
        )

    elif anomaly_score >= 0.50:

        score += 15

        evidence.append(
            "Moderate anomaly score"
        )

    # --------------------------------------------------------
    # 2. ERROR LEVEL
    # --------------------------------------------------------

    level = event.get(
        "level",
        ""
    ).upper()

    if level == "CRITICAL":

        score += 25

        evidence.append(
            "Critical log level"
        )

    elif level == "ERROR":

        score += 20

        evidence.append(
            "Error log level"
        )

    elif level == "WARNING":

        score += 10

        evidence.append(
            "Warning log level"
        )

    # --------------------------------------------------------
    # 3. SEVERITY
    # --------------------------------------------------------

    severity = event.get(
        "severity",
        ""
    ).upper()

    if severity == "CRITICAL":

        score += 20

        evidence.append(
            "Critical incident severity"
        )

    elif severity == "HIGH":

        score += 15

        evidence.append(
            "High incident severity"
        )

    elif severity == "MEDIUM":

        score += 10

        evidence.append(
            "Medium incident severity"
        )

    # --------------------------------------------------------
    # 4. ERROR MESSAGE
    # --------------------------------------------------------

    message = event.get(
        "message",
        ""
    ).lower()

    if any(
        word in message
        for word in [
            "failed",
            "failure",
            "error",
            "timeout",
            "unavailable",
            "exhausted"
        ]
    ):

        score += 15

        evidence.append(
            "Failure-related message"
        )

    # --------------------------------------------------------
    # 5. TEMPORAL POSITION
    # --------------------------------------------------------

    try:

        event_time = parse_timestamp(
            event["timestamp"]
        )

        start_time = parse_timestamp(
            incident_start
        )

        end_time = parse_timestamp(
            incident_end
        )

        duration = (
            end_time - start_time
        ).total_seconds()

        position = (
            event_time - start_time
        ).total_seconds()

        if duration > 0:

            normalized_position = (
                position / duration
            )

            # Early events are more interesting
            # as possible causes.

            if normalized_position <= 0.30:

                score += 20

                evidence.append(
                    "Occurred early in incident"
                )

            elif normalized_position <= 0.50:

                score += 10

                evidence.append(
                    "Occurred near beginning of incident"
                )

    except (
        ValueError,
        TypeError,
        KeyError
    ):

        pass

    return score, evidence


# ============================================================
# ANALYZE ONE INCIDENT
# ============================================================

def analyze_incident(incident):

    events = incident.get(
        "events",
        []
    )

    if not events:

        return {
            "root_cause": "UNKNOWN",
            "confidence": 0.0,
            "evidence": [],
            "candidates": []
        }

    incident_start = incident.get(
        "start_time"
    )

    incident_end = incident.get(
        "end_time"
    )

    candidates = []

    for event in events:

        candidate_type = classify_candidate(
            event
        )

        score, evidence = score_candidate(
            event,
            incident_start,
            incident_end
        )

        candidates.append(
            {
                "candidate_type":
                    candidate_type,

                "service":
                    event.get(
                        "service"
                    ),

                "timestamp":
                    event.get(
                        "timestamp"
                    ),

                "message":
                    event.get(
                        "message"
                    ),

                "score":
                    score,

                "evidence":
                    evidence
            }
        )

    # Sort candidates by score
    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    best = candidates[0]

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    max_score = 120

    confidence = min(
        best["score"] / max_score,
        1.0
    )
    if best["candidate_type"] == "UNKNOWN":
        confidence = min(confidence, 0.20)
    # More evidence improves confidence
    if len(events) >= 3:

        confidence += 0.05

    confidence = min(
        confidence,
        1.0
    )

    # --------------------------------------------------------
    # SINGLE EVENT WARNING
    # --------------------------------------------------------

    if len(events) == 1:

        confidence = min(
            confidence,
            0.40
        )

        root_cause = (
            "INSUFFICIENT_EVIDENCE"
        )

    else:

        root_cause = (
            best["candidate_type"]
        )

    return {

        "root_cause":
            root_cause,

        "root_cause_service":
            best["service"],

        "root_cause_timestamp":
            best["timestamp"],

        "root_cause_message":
            best["message"],

        "confidence":
            round(
                confidence,
                3
            ),

        "evidence":
            best["evidence"],

        "candidates":
            candidates
    }


# ============================================================
# ANALYZE ALL INCIDENTS
# ============================================================

def analyze_all_incidents(
    incidents
):

    results = []

    for incident in incidents:

        analysis = analyze_incident(
            incident
        )

        result = {

            "incident_id":
                incident.get(
                    "incident_id"
                ),

            "start_time":
                incident.get(
                    "start_time"
                ),

            "end_time":
                incident.get(
                    "end_time"
                ),

            "event_count":
                incident.get(
                    "event_count"
                ),

            "services":
                incident.get(
                    "services"
                ),

            "dominant_pattern":
                incident.get(
                    "dominant_pattern"
                ),

            "root_cause":
                analysis[
                    "root_cause"
                ],

            "root_cause_service":
                analysis[
                    "root_cause_service"
                ],

            "root_cause_timestamp":
                analysis[
                    "root_cause_timestamp"
                ],

            "root_cause_message":
                analysis[
                    "root_cause_message"
                ],

            "confidence":
                analysis[
                    "confidence"
                ],

            "evidence":
                analysis[
                    "evidence"
                ],

            "candidates":
                analysis[
                    "candidates"
                ]
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
        "rca_engine/incident_results.json"
    )

    output_file = (
        "rca_engine/root_cause_results.json"
    )

    incidents = load_incidents(
        input_file
    )

    print(
        "=============================================="
    )

    print(
        "       MEMBER 3 - ROOT CAUSE ENGINE"
    )

    print(
        "=============================================="
    )

    print(
        "Total incidents:",
        len(incidents)
    )

    results = analyze_all_incidents(
        incidents
    )

    print(
        "\nROOT CAUSE ANALYSIS"
    )

    print(
        "----------------------------------------------"
    )

    for result in results[:20]:

        print(
            result["incident_id"],
            "|",
            result["root_cause"],
            "| Confidence:",
            result["confidence"]
        )

        print(
            "Service :",
            result["root_cause_service"]
        )

        print(
            "Message :",
            result["root_cause_message"]
        )

        print(
            "Evidence:",
            ", ".join(
                result["evidence"]
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
        "\nRoot cause results saved to:",
        output_file
    )