# ============================================================
# FEATURE CONTRIBUTION
# ============================================================

def get_feature_contributions(row):

    contributions = {}

    # Basic features
    contributions["error_count"] = row.get("error_count", 0)
    contributions["warning_count"] = row.get("warning_count", 0)

    # Message features
    contributions["failed_login"] = row.get("failed_login", 0)
    contributions["database_error"] = row.get("database_error", 0)
    contributions["server_error"] = row.get("server_error", 0)
    contributions["timeout_error"] = row.get("timeout_error", 0)

    # Service
    contributions["critical_service"] = row.get(
        "critical_service", 0
    )

    # Activity
    contributions["requests_per_minute"] = row.get(
        "requests_per_minute", 0
    )

    contributions["errors_per_minute"] = row.get(
        "errors_per_minute", 0
    )

    contributions["failed_logins_per_minute"] = row.get(
        "failed_logins_per_minute", 0
    )

    # Sliding window
    contributions["window_errors"] = row.get(
        "window_errors", 0
    )

    contributions["window_failed_logins"] = row.get(
        "window_failed_logins", 0
    )

    contributions["window_error_rate"] = row.get(
        "window_error_rate", 0
    )

    # Service-specific
    contributions["auth_activity"] = row.get(
        "auth_activity", 0
    )

    contributions["payment_activity"] = row.get(
        "payment_activity", 0
    )

    contributions["db_activity"] = row.get(
        "db_activity", 0
    )

    contributions["api_activity"] = row.get(
        "api_activity", 0
    )

    contributions["order_activity"] = row.get(
        "order_activity", 0
    )

    contributions["inventory_activity"] = row.get(
        "inventory_activity", 0
    )

    # --------------------------------------------------------
    # Sort features by their values
    # --------------------------------------------------------

    sorted_features = sorted(
        contributions.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Keep only meaningful features
    top_features = [
        feature
        for feature, value in sorted_features
        if value > 0
    ]

    return top_features[:5]


def format_contributions(row):

    features = get_feature_contributions(row)

    if not features:
        return "No significant feature contribution"

    return ", ".join(features)