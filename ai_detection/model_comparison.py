import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from feature_engineering import load_logs, create_features


# ============================================================
# 1. LOAD DATASET
# ============================================================

input_file = "ai_detection/data/training_logs.json"

df = load_logs(input_file)

print(f"\nTotal logs loaded: {len(df)}")


# ============================================================
# 2. CREATE FEATURES
# ============================================================

df = create_features(df)

print("\nFeatures created:")
print(df.columns.tolist())


# ============================================================
# 3. SELECT ML FEATURES
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

X = df[features].copy()


# ============================================================
# 4. GROUND TRUTH
# ============================================================

df["actual"] = df["ground_truth"].apply(
    lambda x: 0 if x == "NORMAL" else 1
)


# ============================================================
# 5. MODEL 1 - ISOLATION FOREST
# ============================================================

print("\n==============================================")
print("MODEL 1: ISOLATION FOREST")
print("==============================================")

isolation_forest = IsolationForest(
    n_estimators=100,
    contamination=0.20,
    random_state=42
)

print("\nTraining Isolation Forest...")

isolation_forest.fit(X)

print("Isolation Forest training completed.")


# Predict

if_prediction = isolation_forest.predict(X)

df["if_prediction"] = if_prediction

df["if_predicted"] = df["if_prediction"].apply(
    lambda x: 0 if x == 1 else 1
)


# Anomaly score

df["if_score"] = -isolation_forest.score_samples(X)


# ============================================================
# 6. MODEL 2 - LOCAL OUTLIER FACTOR
# ============================================================

print("\n==============================================")
print("MODEL 2: LOCAL OUTLIER FACTOR")
print("==============================================")

lof = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.20
)

print("\nTraining Local Outlier Factor...")

lof_prediction = lof.fit_predict(X)

print("Local Outlier Factor training completed.")


df["lof_prediction"] = lof_prediction

df["lof_predicted"] = df["lof_prediction"].apply(
    lambda x: 0 if x == 1 else 1
)


# LOF anomaly score
# Negative outlier factor:
# Normal values are closer to -1
# More negative values indicate stronger outliers

df["lof_score"] = -lof.negative_outlier_factor_


# ============================================================
# 7. EVALUATE ISOLATION FOREST
# ============================================================

if_accuracy = accuracy_score(
    df["actual"],
    df["if_predicted"]
)

if_precision = precision_score(
    df["actual"],
    df["if_predicted"],
    zero_division=0
)

if_recall = recall_score(
    df["actual"],
    df["if_predicted"],
    zero_division=0
)

if_f1 = f1_score(
    df["actual"],
    df["if_predicted"],
    zero_division=0
)


# ============================================================
# 8. EVALUATE LOF
# ============================================================

lof_accuracy = accuracy_score(
    df["actual"],
    df["lof_predicted"]
)

lof_precision = precision_score(
    df["actual"],
    df["lof_predicted"],
    zero_division=0
)

lof_recall = recall_score(
    df["actual"],
    df["lof_predicted"],
    zero_division=0
)

lof_f1 = f1_score(
    df["actual"],
    df["lof_predicted"],
    zero_division=0
)


# ============================================================
# 9. MODEL COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame({

    "Model": [
        "Isolation Forest",
        "Local Outlier Factor"
    ],

    "Accuracy": [
        if_accuracy,
        lof_accuracy
    ],

    "Precision": [
        if_precision,
        lof_precision
    ],

    "Recall": [
        if_recall,
        lof_recall
    ],

    "F1-Score": [
        if_f1,
        lof_f1
    ]
})


# ============================================================
# 10. DISPLAY COMPARISON
# ============================================================

print("\n==============================================")
print("MODEL COMPARISON RESULTS")
print("==============================================\n")

print(
    comparison.to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}"
    )
)


# ============================================================
# 11. ISOLATION FOREST REPORT
# ============================================================

print("\n==============================================")
print("ISOLATION FOREST CLASSIFICATION REPORT")
print("==============================================\n")

print(
    classification_report(
        df["actual"],
        df["if_predicted"],
        target_names=[
            "NORMAL",
            "ANOMALY"
        ],
        zero_division=0
    )
)


# ============================================================
# 12. LOF REPORT
# ============================================================

print("\n==============================================")
print("LOCAL OUTLIER FACTOR CLASSIFICATION REPORT")
print("==============================================\n")

print(
    classification_report(
        df["actual"],
        df["lof_predicted"],
        target_names=[
            "NORMAL",
            "ANOMALY"
        ],
        zero_division=0
    )
)


# ============================================================
# 13. CONFUSION MATRICES
# ============================================================

print("\n==============================================")
print("ISOLATION FOREST CONFUSION MATRIX")
print("==============================================")

print(
    confusion_matrix(
        df["actual"],
        df["if_predicted"]
    )
)


print("\n==============================================")
print("LOF CONFUSION MATRIX")
print("==============================================")

print(
    confusion_matrix(
        df["actual"],
        df["lof_predicted"]
    )
)


# ============================================================
# 14. SELECT BEST MODEL
# ============================================================

if if_f1 >= lof_f1:

    best_model = "Isolation Forest"
    best_f1 = if_f1

else:

    best_model = "Local Outlier Factor"
    best_f1 = lof_f1


print("\n==============================================")
print("BEST MODEL")
print("==============================================")

print(f"Best model : {best_model}")
print(f"F1-Score   : {best_f1:.3f}")


# ============================================================
# 15. MODEL COMPARISON SUMMARY
# ============================================================

print("\n==============================================")
print("MODEL COMPARISON COMPLETED")
print("==============================================")

print("""
Isolation Forest:
- Detects global anomalies
- Works well with high-dimensional features
- Suitable for large log datasets

Local Outlier Factor:
- Detects local anomalies
- Compares each log with its neighboring logs
- Useful for detecting unusual local behavior
""")