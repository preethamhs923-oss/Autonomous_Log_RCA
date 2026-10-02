import os
import sys
import joblib

from sklearn.ensemble import IsolationForest

# ------------------------------------------------------------
# Allow Python to find feature_engineering.py
# ------------------------------------------------------------

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from feature_engineering import load_logs, create_features


# ============================================================
# 1. LOAD DATA
# ============================================================

input_file = "ai_detection/data/training_logs.json"

df = load_logs(input_file)

print(f"\nTotal logs loaded: {len(df)}")


# ============================================================
# 2. CREATE FEATURES
# ============================================================

df = create_features(df)

print("\nFeatures created successfully.")


# ============================================================
# 3. SELECT FEATURES
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

X = df[features]


# ============================================================
# 4. CREATE MODEL
# ============================================================

model = IsolationForest(
    n_estimators=100,
    contamination=0.20,
    random_state=42
)


# ============================================================
# 5. TRAIN MODEL
# ============================================================

print("\nTraining Isolation Forest...")

model.fit(X)

print("Model training completed.")


# ============================================================
# 6. SAVE MODEL
# ============================================================

model_directory = "ai_detection/models"

os.makedirs(
    model_directory,
    exist_ok=True
)

model_file = (
    "ai_detection/models/"
    "isolation_forest_model.joblib"
)

joblib.dump(
    model,
    model_file
)

print(
    f"\nModel saved successfully to:"
    f"\n{model_file}"
)


# ============================================================
# 7. LOAD MODEL
# ============================================================

print("\nLoading saved model...")

loaded_model = joblib.load(
    model_file
)

print("Model loaded successfully.")


# ============================================================
# 8. TEST LOADED MODEL
# ============================================================

predictions = loaded_model.predict(X)

anomaly_count = (
    predictions == -1
).sum()

normal_count = (
    predictions == 1
).sum()


# ============================================================
# 9. DISPLAY RESULTS
# ============================================================

print("\n===== LOADED MODEL TEST =====")

print(
    f"Total logs     : {len(df)}"
)

print(
    f"Normal logs    : {normal_count}"
)

print(
    f"Anomaly logs   : {anomaly_count}"
)


# ============================================================
# 10. VERIFY MODEL
# ============================================================

if len(predictions) == len(df):

    print(
        "\nMODEL SAVE/LOAD TEST: SUCCESS"
    )

else:

    print(
        "\nMODEL SAVE/LOAD TEST: FAILED"
    )