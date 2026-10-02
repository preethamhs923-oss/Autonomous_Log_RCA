def apply_rules(row):

    reasons = []

    # Rule 1: Failed login activity
    if row["failed_login"] >= 1:
        reasons.append("Failed login detected")

    # Rule 2: High failed login activity
    if row["failed_logins_per_minute"] >= 3:
        reasons.append("High failed login frequency")

    # Rule 3: Database problems
    if row["database_error"] == 1:
        reasons.append("Database error detected")

    # Rule 4: Timeout
    if row["timeout_error"] == 1:
        reasons.append("Timeout detected")

    # Rule 5: Server error
    if row["server_error"] == 1:
        reasons.append("Server error detected")

    # Rule 6: High error rate
    if row["error_rate"] >= 0.5:
        reasons.append("High error rate")

    # Rule 7: High activity in sliding window
    if row["window_requests"] >= 20:
        reasons.append("High request activity")

    # Rule 8: Multiple errors in window
    if row["window_errors"] >= 5:
        reasons.append("Repeated errors in time window")

    # Final rule result
    if len(reasons) > 0:
        rule_anomaly = True
    else:
        rule_anomaly = False

    return rule_anomaly, reasons