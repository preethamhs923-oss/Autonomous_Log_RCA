# ============================================================
# EXPLAINABLE ANOMALY DETECTION
# ============================================================

def explain_anomaly(row):

    reasons = []

    # Error
    if row.get("error_count", 0) == 1:
        reasons.append("ERROR log detected")

    if row.get("warning_count", 0) == 1:
        reasons.append("WARNING log detected")

    # Authentication
    if row.get("failed_login", 0) == 1:
        reasons.append("Failed login activity detected")

    # Database
    if row.get("database_error", 0) == 1:
        reasons.append("Database-related error detected")

    # Server
    if row.get("server_error", 0) == 1:
        reasons.append("Server error detected")

    # Timeout
    if row.get("timeout_error", 0) == 1:
        reasons.append("Timeout detected")

    # Time-based activity
    if row.get("requests_per_minute", 0) >= 10:
        reasons.append("High request rate detected")

    if row.get("errors_per_minute", 0) >= 3:
        reasons.append("High error activity detected")

    if row.get("failed_logins_per_minute", 0) >= 3:
        reasons.append("Multiple failed logins detected")

    # Sliding window
    if row.get("window_errors", 0) >= 3:
        reasons.append("Multiple errors in 5-minute window")

    if row.get("window_failed_logins", 0) >= 3:
        reasons.append("Multiple failed logins in 5-minute window")

    # Critical service
    if row.get("critical_service", 0) == 1:
        reasons.append("Critical service involved")

    # Service-specific features
    if row.get("auth_activity", 0) == 1:
        reasons.append("Suspicious authentication activity")

    if row.get("payment_activity", 0) == 1:
        reasons.append("Suspicious payment activity")

    if row.get("db_activity", 0) == 1:
        reasons.append("Suspicious database activity")

    if row.get("api_activity", 0) == 1:
        reasons.append("Suspicious API gateway activity")

    if row.get("order_activity", 0) == 1:
        reasons.append("Suspicious order activity")

    if row.get("inventory_activity", 0) == 1:
        reasons.append("Suspicious inventory activity")

    # Anomaly score
    score = row.get("anomaly_score", 0)

    if score >= 0.60:
        reasons.append("Very high anomaly score")

    elif score >= 0.50:
        reasons.append("High anomaly score")

    # Default
    if not reasons:
        reasons.append(
            "Unusual combination of log features detected"
        )

    return reasons


# ============================================================
# GET FINAL EXPLANATION
# ============================================================

def get_explanation(row):

    reasons = explain_anomaly(row)

    return "; ".join(reasons)