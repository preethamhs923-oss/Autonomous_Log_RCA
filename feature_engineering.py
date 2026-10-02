import json
import pandas as pd


def load_logs(file_path):
    with open(file_path, "r") as f:
        logs = json.load(f)

    return pd.DataFrame(logs)


def create_features(df):

    # =========================================================
    # 1. BASIC FEATURES
    # =========================================================

    df["error_count"] = (
        df["level"] == "ERROR"
    ).astype(int)

    df["warning_count"] = (
        df["level"] == "WARNING"
    ).astype(int)


    # =========================================================
    # 2. MESSAGE FEATURES
    # =========================================================

    df["message"] = df["message"].fillna("")

    df["message_length"] = df["message"].str.len()

    message_lower = df["message"].str.lower()

    df["failed_login"] = (
        message_lower.str.contains(
            "login failed|invalid credentials|authentication failed",
            na=False
        )
    ).astype(int)

    df["database_error"] = (
        message_lower.str.contains(
            "database|db timeout|connection pool",
            na=False
        )
    ).astype(int)

    df["server_error"] = (
        message_lower.str.contains(
            "server error|internal server|service unavailable",
            na=False
        )
    ).astype(int)

    df["timeout_error"] = (
        message_lower.str.contains(
            "timeout|timed out",
            na=False
        )
    ).astype(int)


    # =========================================================
    # 3. SERVICE FEATURES
    # =========================================================

    df["critical_service"] = (
        df["service"].isin([
            "payment-service",
            "database-service",
            "api-gateway"
        ])
    ).astype(int)


    # =========================================================
    # 4. IP ACTIVITY
    # =========================================================

    df["ip_frequency"] = (
        df.groupby("source_ip")["source_ip"]
        .transform("count")
    )


    # =========================================================
    # 5. TIME-BASED FEATURES
    # =========================================================

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["time_minute"] = (
        df["timestamp"].dt.floor("min")
    )


    # Requests per minute
    df["requests_per_minute"] = (
        df.groupby(
            ["service", "time_minute"]
        )["service"].transform("count")
    )


    # Errors per minute
    df["errors_per_minute"] = (
        df.groupby(
            ["service", "time_minute"]
        )["error_count"].transform("sum")
    )


    # Failed logins per minute
    df["failed_logins_per_minute"] = (
        df.groupby(
            ["service", "time_minute"]
        )["failed_login"].transform("sum")
    )


    # Error rate
    df["error_rate"] = (
        df["errors_per_minute"] /
        df["requests_per_minute"]
    )

    df["error_rate"] = df["error_rate"].fillna(0)


    # =========================================================
    # 6. SLIDING WINDOW FEATURES
    # =========================================================

    # Sort by service and timestamp
    df = df.sort_values(
        ["service", "timestamp"]
    ).reset_index(drop=True)


    # Create 5-minute rolling features
    df["window_requests"] = 0.0
    df["window_errors"] = 0.0
    df["window_failed_logins"] = 0.0


    for service in df["service"].unique():

        service_mask = df["service"] == service

        service_data = df.loc[
            service_mask
        ].copy()

        service_data = service_data.set_index(
            "timestamp"
        )

        # Requests in previous 5 minutes
        requests = (
            service_data["service"]
            .rolling("5min")
            .count()
        )

        # Errors in previous 5 minutes
        errors = (
            service_data["error_count"]
            .rolling("5min")
            .sum()
        )

        # Failed logins in previous 5 minutes
        failed_logins = (
            service_data["failed_login"]
            .rolling("5min")
            .sum()
        )

        df.loc[
            service_mask,
            "window_requests"
        ] = requests.values

        df.loc[
            service_mask,
            "window_errors"
        ] = errors.values

        df.loc[
            service_mask,
            "window_failed_logins"
        ] = failed_logins.values


    # Window error rate
    df["window_error_rate"] = (
        df["window_errors"] /
        df["window_requests"]
    )

    df["window_error_rate"] = (
        df["window_error_rate"].fillna(0)
    )
        # =========================================================
    # 8. REMOVE TEMPORARY COLUMN

    # =========================================================

    # Authentication activity
    df["auth_activity"] = (
        (df["service"] == "auth-service") &
        (df["failed_login"] == 1)
    ).astype(int)


    # Payment activity
    df["payment_activity"] = (
        (df["service"] == "payment-service") &
        (
            (df["timeout_error"] == 1) |
            (df["database_error"] == 1) |
            (df["error_count"] == 1)
        )
    ).astype(int)


    # Database activity
    df["db_activity"] = (
        (df["service"] == "database-service") &
        (
            (df["database_error"] == 1) |
            (df["timeout_error"] == 1) |
            (df["error_count"] == 1)
        )
    ).astype(int)


    # API Gateway activity
    df["api_activity"] = (
        (df["service"] == "api-gateway") &
        (
            (df["server_error"] == 1) |
            (df["error_count"] == 1)
        )
    ).astype(int)


    # Order service activity
    df["order_activity"] = (
        (df["service"] == "order-service") &
        (
            (df["error_count"] == 1) |
            (df["warning_count"] == 1)
        )
    ).astype(int)


    # Inventory service activity
    df["inventory_activity"] = (
        (df["service"] == "inventory-service") &
        (
            (df["warning_count"] == 1) |
            (df["error_count"] == 1)
        )
    ).astype(int)


    # =========================================================
    # 7. REMOVE TEMPORARY COLUMN
    # =========================================================

    df.drop(
        columns=["time_minute"],
        inplace=True
    )


    return df


# =============================================================
# TEST FEATURE ENGINEERING
# =============================================================

if __name__ == "__main__":

    input_file = "ai_detection/data/training_logs.json"

    df = load_logs(input_file)

    df = create_features(df)


    print("\n===== FEATURE ENGINEERING OUTPUT =====\n")

    print(df.head())


    print("\n===== FEATURES CREATED =====\n")

    print(df.columns.tolist())


    print("\n===== TIME-BASED FEATURES =====\n")

    print(
        df[
            [
                "timestamp",
                "service",
                "requests_per_minute",
                "errors_per_minute",
                "failed_logins_per_minute",
                "error_rate"
            ]
        ].head(20).to_string(index=False)
    )


    print("\n===== SLIDING WINDOW FEATURES =====\n")

    print(
        df[
            [
                "timestamp",
                "service",
                "window_requests",
                "window_errors",
                "window_failed_logins",
                "window_error_rate"
            ]
        ].head(20).to_string(index=False)
    )
    print("\n===== SERVICE-SPECIFIC FEATURES =====\n")

    print(
        df[
            [
                "service",
                "auth_activity",
                "payment_activity",
                "db_activity",
                "api_activity",
                "order_activity",
                "inventory_activity"
            ]
        ].head(20).to_string(index=False)
    )