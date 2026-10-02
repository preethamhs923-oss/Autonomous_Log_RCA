import os
import sys
import joblib
import pandas as pd

# Allow Python to find project files
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from feature_engineering import create_features


# ============================================================
# 1. LOAD TRAINED MODEL
# ============================================================

model_file = "ai_detection/models/isolation_forest_model.joblib"

model = joblib.load(model_file)

print("\nModel loaded successfully.")


# ============================================================
# 2. FEATURES USED BY MODEL
# ============================================================

features = [
    "error_count",
    "warning_count",
    "message_length",
    "failed_login",
    "database_error",
    "server_error",
    "timeout_error",
    "critical_service",
    "ip_frequency",
    "requests_per_minute",
    "errors_per_minute",
    "failed_logins_per_minute",
    "error_rate",
    "window_requests",
    "window_errors",
    "window_failed_logins",
    "window_error_rate",
    "auth_activity",
    "payment_activity",
    "db_activity",
    "api_activity",
    "order_activity",
    "inventory_activity"
]


# ============================================================
# 3. FUNCTION FOR REAL-TIME LOG PREDICTION
# ============================================================

def predict_log(log):

    # Convert log into DataFrame
    df = pd.DataFrame([log])

    # Create features
    df = create_features(df)

    # Select ML features
    X = df[features]

    # Prediction
    prediction = model.predict(X)[0]

    # Anomaly score
    anomaly_score = -model.score_samples(X)[0]

    # Status
    if prediction == -1:
        status = "ANOMALY"
    else:
        status = "NORMAL"

    return {
        "timestamp": log["timestamp"],
        "service": log["service"],
        "level": log["level"],
        "message": log["message"],
        "anomaly_score": round(float(anomaly_score), 6),
        "status": status
    }


# ============================================================
# 4. TEST REAL-TIME LOG
# ============================================================

new_log = {
    "timestamp": "2026-08-24 12:10:30",
    "service": "payment-service",
    "level": "ERROR",
    "message": "Database connection timeout",
    "source_ip": "192.168.1.100",
    "trace_id": "REALTIME-001"
}


# ============================================================
# 5. PREDICT
# ============================================================

result = predict_log(new_log)


# ============================================================
# 6. DISPLAY RESULT
# ============================================================

print("\n==============================================")
print("REAL-TIME LOG PREDICTION")
print("==============================================")

print(f"Timestamp      : {result['timestamp']}")
print(f"Service        : {result['service']}")
print(f"Level          : {result['level']}")
print(f"Message        : {result['message']}")
print(f"Anomaly Score  : {result['anomaly_score']}")
print(f"Status         : {result['status']}")

print("==============================================")