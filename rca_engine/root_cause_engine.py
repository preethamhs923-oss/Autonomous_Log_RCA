
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "incident_results.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "root_cause_results.json")


# ============================================================
# CONFIGURATION
# ============================================================

# Heuristic confidence indicators, not calibrated probabilities.
CONFIDENCE_LABELS = [
    (0.75, "HIGH"),
    (0.45, "MODERATE"),
    (0.0, "LOW"),
]

FAILURE_KEYWORDS = (
    "failed", "failure", "error", "timeout", "timed out",
    "unavailable", "exhausted", "refused", "rejected",
)

ROOT_CAUSE_ACTIONS = {
    "DATABASE_FAILURE": [
        "Inspect database availability and connection-pool saturation.",
        "Check slow queries, database locks, and connection limits.",
        "Review database connectivity and database error logs.",
    ],
    "AUTHENTICATION_FAILURE": [
        "Inspect authentication-provider availability.",
        "Verify token expiry and credential configuration.",
        "Review failed-login patterns and identity-provider connectivity.",
    ],
    "TIMEOUT_FAILURE": [
        "Measure request latency and identify slow dependencies.",
        "Inspect timeout settings and worker saturation.",
        "Check retries, queue backlogs, and downstream response times.",
    ],
    "SERVICE_FAILURE": [
        "Check service health and recent deployment history.",
        "Inspect application exceptions and dependency failures.",
        "Review CPU, memory, and worker utilization.",
    ],
    "API_FAILURE": [
        "Inspect API gateway and upstream-service error rates.",
        "Verify routing, endpoint availability, and upstream responses.",
        "Review recent API configuration and rate-limit changes.",
    ],
    "RESOURCE_OVERLOAD": [
        "Inspect CPU, memory, disk, and worker-pool utilization.",
        "Identify traffic spikes, resource leaks, or capacity exhaustion.",
        "Consider scaling or rate limiting after confirming the bottleneck.",
    ],
    "UNKNOWN": [
        "Inspect the incident timeline and collect additional logs.",
        "Correlate trace IDs and request IDs across affected services.",
        "Collect more evidence before applying corrective actions.",
    ],
}


# ============================================================
# LOAD INCIDENTS
# ============================================================

def load_incidents(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Incident file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Expected incident_results.json to contain a JSON list."
        )

    return data


# ============================================================
# TIMESTAMP UTILITIES
# ============================================================

def parse_timestamp(timestamp):

    if isinstance(timestamp, datetime):
        return timestamp

    if timestamp is None:
        return None

    value = str(timestamp).strip()

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        pass

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def timestamp_seconds(value):

    parsed = parse_timestamp(value)

    if parsed is None:
        return None

    if parsed.tzinfo is not None:
        return parsed.timestamp()

    return parsed.replace(
        tzinfo=timezone.utc
    ).timestamp()


# ============================================================
# ROOT CAUSE CLASSIFICATION
# ============================================================

def classify_candidate(event):

    message = str(
        event.get("message") or ""
    ).lower()

    pattern = str(
        event.get("pattern") or ""
    ).strip()

    rules = [

        ("DATABASE_FAILURE", [
            "database",
            "connection pool",
            "database connection",
            "sql",
            "query failed",
            "db connection",
        ]),

        ("AUTHENTICATION_FAILURE", [
            "failed login",
            "login failed",
            "authentication failed",
            "invalid credentials",
            "invalid password",
            "unauthorized",
            "access denied",
            "authentication error",
            "authentication failure",
        ]),

        ("RESOURCE_OVERLOAD", [
            "resource exhausted",
            "too many requests",
            "high traffic",
            "overload",
            "out of memory",
            "memory exhausted",
            "cpu limit",
            "rate limit",
        ]),

        ("TIMEOUT_FAILURE", [
            "timeout",
            "timed out",
            "deadline exceeded",
        ]),

        ("API_FAILURE", [
            "api error",
            "gateway error",
            "bad gateway",
            "request failed",
            "upstream error",
        ]),

        ("SERVICE_FAILURE", [
            "service unavailable",
            "service failed",
            "internal server error",
            "server error",
            "service down",
            "process crashed",
        ]),
    ]

    for candidate_type, keywords in rules:

        if any(
            keyword in message
            for keyword in keywords
        ):
            return candidate_type

    return pattern if pattern else "UNKNOWN"


# ============================================================
# SCORE ROOT CAUSE CANDIDATE
# ============================================================

def score_candidate(
    event,
    incident_start=None,
    incident_end=None
):

    score = 0
    evidence = []

    # 1. ANOMALY SCORE

    try:
        anomaly_score = float(
            event.get("anomaly_score", 0) or 0
        )
    except (ValueError, TypeError):
        anomaly_score = 0.0

    # Support both 0-1 and 0-100 scales.
    if anomaly_score > 1:
        anomaly_score /= 100.0

    if anomaly_score >= 0.80:
        score += 25
        evidence.append("Very high anomaly score")

    elif anomaly_score >= 0.60:
        score += 20
        evidence.append("High anomaly score")

    elif anomaly_score >= 0.50:
        score += 10
        evidence.append("Moderate anomaly score")

    # 2. LOG LEVEL

    level = str(
        event.get("level") or ""
    ).upper()

    if level in ("CRITICAL", "FATAL"):
        score += 20
        evidence.append(f"{level} log level")

    elif level == "ERROR":
        score += 15
        evidence.append("ERROR log level")

    elif level in ("WARNING", "WARN"):
        score += 7
        evidence.append("WARNING log level")

    # 3. SEVERITY

    severity = str(
        event.get("severity") or ""
    ).upper()

    if severity == "CRITICAL":
        score += 15
        evidence.append("Critical severity")

    elif severity == "HIGH":
        score += 12
        evidence.append("High severity")

    elif severity == "MEDIUM":
        score += 7
        evidence.append("Medium severity")

    # 4. FAILURE MESSAGE

    message = str(
        event.get("message") or ""
    ).lower()

    matched_words = [
        word for word in FAILURE_KEYWORDS
        if word in message
    ]

    if matched_words:
        score += 10
        evidence.append(
            "Failure indicators: "
            + ", ".join(matched_words[:3])
        )

    # 5. TEMPORAL POSITION

    event_time = timestamp_seconds(
        event.get("timestamp")
    )

    start_time = timestamp_seconds(
        incident_start
    )

    end_time = timestamp_seconds(
        incident_end
    )

    if event_time is not None and start_time is not None:

        if end_time is not None and end_time > start_time:

            position = (
                (event_time - start_time)
                / (end_time - start_time)
            )

            if 0 <= position <= 0.20:
                score += 15
                evidence.append(
                    "Occurred in first 20% of incident"
                )

            elif 0 <= position <= 0.40:
                score += 8
                evidence.append(
                    "Occurred early in incident"
                )

        elif event_time == start_time:
            score += 8
            evidence.append(
                "Occurred at incident start"
            )

    return score, evidence


# ============================================================
# GROUP RELATED ROOT CAUSE CANDIDATES
# ============================================================

def build_ranked_candidates(
    events,
    incident_start,
    incident_end
):

    grouped = defaultdict(list)

    for event in events:

        candidate_type = classify_candidate(event)

        service = str(
            event.get("service") or "unknown-service"
        )

        score, evidence = score_candidate(
            event,
            incident_start,
            incident_end,
        )

        grouped[
            (candidate_type, service)
        ].append({

            "timestamp": event.get("timestamp"),
            "message": event.get("message"),
            "score": score,
            "evidence": evidence,

        })

    candidates = []

    for (candidate_type, service), records in grouped.items():

        best_event = max(
            records,
            key=lambda item: item["score"]
        )

        # Repeated supporting events increase candidate score.
        support_bonus = min(
            max(len(records) - 1, 0) * 3,
            12
        )

        evidence = list(
            best_event["evidence"]
        )

        if len(records) > 1:
            evidence.append(
                f"{len(records)} related events support this candidate"
            )

        supporting_events = sorted(
            records,
            key=lambda item: (
                timestamp_seconds(item.get("timestamp"))
                if timestamp_seconds(item.get("timestamp")) is not None
                else float("inf")
            ),
        )

        candidates.append({

            "candidate_type": candidate_type,

            "service": service,

            "score": (
                best_event["score"] + support_bonus
            ),

            "event_count": len(records),

            "timestamp": best_event.get("timestamp"),

            "message": best_event.get("message"),

            "evidence": evidence,

            "supporting_events": [
                {
                    "timestamp": item.get("timestamp"),
                    "message": item.get("message"),
                    "score": item.get("score"),
                }
                for item in supporting_events
            ],

        })

    candidates.sort(
        key=lambda item: (
            item["score"],
            item["event_count"]
        ),
        reverse=True,
    )

    return candidates


# ============================================================
# CONFIDENCE CALCULATION
# ============================================================

def calculate_confidence(
    candidates,
    total_events
):

    if not candidates or total_events == 0:
        return 0.0, "LOW"

    best = candidates[0]

    best_score = float(
        best["score"]
    )

    second_score = (
        float(candidates[1]["score"])
        if len(candidates) > 1
        else 0.0
    )

    # Score strength

    score_strength = min(
        best_score / 85.0,
        1.0
    )

    # Supporting event strength

    support_strength = min(
        best["event_count"] / 3.0,
        1.0
    )

    # Difference between the top two candidates

    if len(candidates) > 1:

        separation = max(
            0.0,
            (best_score - second_score)
            / max(best_score, 1.0)
        )

    else:
        separation = 0.5

    confidence = (
        0.50 * score_strength
        + 0.30 * support_strength
        + 0.20 * separation
    )

    if best["candidate_type"] == "UNKNOWN":
        confidence = min(confidence, 0.20)

    if total_events == 1:
        confidence = min(confidence, 0.35)

    confidence = round(
        max(0.0, min(confidence, 1.0)),
        3
    )

    label = next(
        (
            name
            for threshold, name in CONFIDENCE_LABELS
            if confidence >= threshold
        ),
        "LOW",
    )

    return confidence, label


# ============================================================
# ANALYZE ONE INCIDENT
# ============================================================

def analyze_incident(incident):

    events = incident.get("events") or []

    if not isinstance(events, list) or not events:

        return {

            "root_cause": "UNKNOWN",

            "root_cause_service": None,

            "root_cause_timestamp": None,

            "root_cause_message": None,

            "confidence": 0.0,

            "confidence_level": "LOW",

            "evidence": [
                "No events available for analysis"
            ],

            "candidates": [],

            "recommended_actions": (
                ROOT_CAUSE_ACTIONS["UNKNOWN"]
            ),

            "analysis_method": (
                "Evidence-based heuristic ranking"
            ),

        }

    candidates = build_ranked_candidates(
        events,
        incident.get("start_time"),
        incident.get("end_time"),
    )

    best = candidates[0] if candidates else None

    if best is None:

        root_cause = "UNKNOWN"
        confidence = 0.0
        confidence_level = "LOW"

        service = None
        timestamp = None
        message = None

        evidence = [
            "No classifiable candidate events were found"
        ]

        action_key = "UNKNOWN"

    else:

        confidence, confidence_level = calculate_confidence(
            candidates,
            len(events),
        )

        if len(events) == 1:

            root_cause = "INSUFFICIENT_EVIDENCE"

            evidence = list(
                best["evidence"]
            )

            evidence.append(
                "Only one event is available; "
                "additional correlated telemetry is required"
            )

        else:

            root_cause = best["candidate_type"]

            evidence = list(
                best["evidence"]
            )

        service = best["service"]

        timestamp = best["timestamp"]

        message = best["message"]

        action_key = (
            best["candidate_type"]
            if best["candidate_type"] in ROOT_CAUSE_ACTIONS
            else "UNKNOWN"
        )

    return {

        "root_cause": root_cause,

        "root_cause_service": service,

        "root_cause_timestamp": timestamp,

        "root_cause_message": message,

        "confidence": confidence,

        "confidence_level": confidence_level,

        "evidence": evidence,

        "candidates": candidates,

        "recommended_actions": (
            ROOT_CAUSE_ACTIONS[action_key]
        ),

        "analysis_method": (
            "Evidence-based heuristic ranking"
        ),

    }


# ============================================================
# ANALYZE ALL INCIDENTS
# ============================================================

def analyze_all_incidents(incidents):

    results = []

    for incident in incidents:

        analysis = analyze_incident(incident)

        result = {

            "incident_id": incident.get("incident_id"),

            "start_time": incident.get("start_time"),

            "end_time": incident.get("end_time"),

            "event_count": incident.get(
                "event_count",
                len(incident.get("events") or [])
            ),

            "services": incident.get("services", []),

            "dominant_pattern": incident.get(
                "dominant_pattern"
            ),

            "root_cause": analysis["root_cause"],

            "root_cause_service": (
                analysis["root_cause_service"]
            ),

            "root_cause_timestamp": (
                analysis["root_cause_timestamp"]
            ),

            "root_cause_message": (
                analysis["root_cause_message"]
            ),

            "confidence": analysis["confidence"],

            "confidence_level": (
                analysis["confidence_level"]
            ),

            "evidence": analysis["evidence"],

            "candidates": analysis["candidates"],

            "recommended_actions": (
                analysis["recommended_actions"]
            ),

            "analysis_method": (
                analysis["analysis_method"]
            ),

        }

        results.append(result)

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    incidents = load_incidents(INPUT_FILE)

    print("=" * 55)

    print(
        "       AUTONOMOUS LOG RCA - ROOT CAUSE ENGINE"
    )

    print("=" * 55)

    print(
        "Total incidents:",
        len(incidents)
    )

    results = analyze_all_incidents(incidents)

    print("\nROOT CAUSE ANALYSIS")

    print("-" * 55)

    for result in results[:20]:

        print(
            result["incident_id"],
            "|",
            result["root_cause"],
            "| Confidence:",
            result["confidence"],
            "(" + result["confidence_level"] + ")",
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
            "; ".join(result["evidence"])
        )

        print(
            "Actions :",
            "; ".join(
                result["recommended_actions"][:2]
            )
        )

        print("-" * 55)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\nRoot cause results saved to:",
        OUTPUT_FILE
    )
