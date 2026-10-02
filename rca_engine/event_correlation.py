import json
from datetime import datetime


def load_logs(file_path):
    """Load all logs from Member 2 output."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_timestamp(timestamp):
    """Convert timestamp string to datetime."""

    return datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )


def calculate_correlation(anomaly, log, time_window_seconds=120):
    """
    Calculate how strongly a log is related to an anomaly.
    """

    try:
        anomaly_time = parse_timestamp(anomaly["timestamp"])
        log_time = parse_timestamp(log["timestamp"])
    except (ValueError, TypeError, KeyError):
        return None

    time_difference = (
        log_time - anomaly_time
    ).total_seconds()

    absolute_difference = abs(time_difference)

    # Ignore events outside time window
    if absolute_difference > time_window_seconds:
        return None

    score = 0
    reasons = []

    # -----------------------------------------
    # 1. SAME TRACE ID
    # -----------------------------------------

    if (
        anomaly.get("trace_id")
        and log.get("trace_id") == anomaly.get("trace_id")
    ):
        score += 50
        reasons.append("same_trace_id")

    # -----------------------------------------
    # 2. SAME SERVICE
    # -----------------------------------------

    if (
        anomaly.get("service")
        and log.get("service") == anomaly.get("service")
    ):
        score += 20
        reasons.append("same_service")

    # -----------------------------------------
    # 3. SAME SOURCE IP
    # -----------------------------------------

    if (
        anomaly.get("source_ip")
        and log.get("source_ip") == anomaly.get("source_ip")
    ):
        score += 15
        reasons.append("same_source_ip")

    # -----------------------------------------
    # 4. ERROR / WARNING LEVEL
    # -----------------------------------------

    if log.get("level") in ["ERROR", "CRITICAL", "WARNING"]:
        score += 10
        reasons.append("error_or_warning")

    # -----------------------------------------
    # 5. TIME PROXIMITY
    # -----------------------------------------

    if absolute_difference <= 30:
        score += 5
        reasons.append("very_close_timestamp")

    # -----------------------------------------
    # 6. EVENT DIRECTION
    # -----------------------------------------

    if time_difference < 0:
        event_relation = "BEFORE_ANOMALY"
    elif time_difference > 0:
        event_relation = "AFTER_ANOMALY"
    else:
        event_relation = "SAME_TIME"

    # -----------------------------------------
    # CORRELATION STRENGTH
    # -----------------------------------------

    if score >= 50:
        strength = "STRONG"

    elif score >= 30:
        strength = "MEDIUM"

    elif score > 0:
        strength = "WEAK"

    else:
        return None

    return {
        "timestamp": log.get("timestamp"),
        "service": log.get("service"),
        "level": log.get("level"),
        "message": log.get("message"),
        "source_ip": log.get("source_ip"),
        "trace_id": log.get("trace_id"),

        "time_difference_seconds": time_difference,

        "event_relation": event_relation,

        "correlation_score": score,

        "correlation_strength": strength,

        "correlation_reasons": reasons
    }


def correlate_events(
    anomaly,
    all_logs,
    time_window_seconds=120
):
    """
    Find and score events related to an anomaly.
    """

    related_events = []

    for log in all_logs:

        # Skip the anomaly itself
        if log is anomaly:
            continue

        result = calculate_correlation(
            anomaly,
            log,
            time_window_seconds
        )

        if result:
            related_events.append(result)

    # Sort by timestamp
    related_events.sort(
        key=lambda x: x["timestamp"]
    )

    return related_events


if __name__ == "__main__":

    input_file = "ai_detection/output/anomaly_results.json"

    logs = load_logs(input_file)

    anomalies = [
        log
        for log in logs
        if log.get("final_status") == "ANOMALY"
    ]

    print("==============================================")
    print("       MEMBER 3 - ADVANCED CORRELATION")
    print("==============================================")

    print("Total logs      :", len(logs))
    print("Total anomalies :", len(anomalies))

    if anomalies:

        anomaly = anomalies[0]

        print("\nSELECTED ANOMALY")
        print("----------------------------------------------")

        print("Timestamp :", anomaly.get("timestamp"))
        print("Service   :", anomaly.get("service"))
        print("Message   :", anomaly.get("message"))
        print("Trace ID  :", anomaly.get("trace_id"))
        print("Severity  :", anomaly.get("severity"))

        related = correlate_events(
            anomaly,
            logs
        )

        print("\nRelated events found:", len(related))

        print("\nCORRELATED EVENT TIMELINE")
        print("----------------------------------------------")

        for event in related:

            print(
                event["timestamp"],
                "|",
                event["event_relation"],
                "|",
                event["service"],
                "|",
                event["level"],
                "|",
                "Score:",
                event["correlation_score"],
                "|",
                event["correlation_strength"],
                "|",
                event["message"]
            )

        # -----------------------------------------
        # SHOW STRONG EVENTS
        # -----------------------------------------

        strong_events = [
            event
            for event in related
            if event["correlation_strength"] == "STRONG"
        ]

        print("\nSTRONG CORRELATIONS")
        print("----------------------------------------------")

        if strong_events:

            for event in strong_events:

                print(
                    event["timestamp"],
                    "|",
                    event["event_relation"],
                    "|",
                    event["message"],
                    "| Score:",
                    event["correlation_score"]
                )

        else:

            print("No strong correlations found.")