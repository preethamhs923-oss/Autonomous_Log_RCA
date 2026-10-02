from ai_detection.feature_contribution import format_contributions
from ai_detection.explainability import get_explanation
import json
import os

from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix

from rule_engine import apply_rules
from ai_detection.explainability import get_explanation
from feature_engineering import load_logs, create_features


# ============================================================
# 1. LOAD TRAINING DATASET
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
# 3. SELECT FEATURES FOR MACHINE LEARNING
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
    "ip_frequency"
]

X = df[features]


# ============================================================
# 4. CREATE ISOLATION FOREST MODEL
# ============================================================

model = IsolationForest(
    n_estimators=100,
    contamination=0.20,
    random_state=42
)


# ============================================================
# 5. TRAIN MODEL
# ============================================================

print("\nTraining Isolation Forest model...")

model.fit(X)

print("Model training completed.")


# ============================================================
# 6. PREDICT ANOMALIES
# ============================================================

df["prediction"] = model.predict(X)


# ============================================================
# 7. CALCULATE ANOMALY SCORE
# ============================================================

df["anomaly_score"] = -model.score_samples(X)
# ============================================================
# DYNAMIC ANOMALY THRESHOLD
# ============================================================

# Calculate threshold from the anomaly-score distribution
dynamic_threshold = df["anomaly_score"].quantile(0.80)

print(
    f"\nDynamic anomaly threshold: {dynamic_threshold:.6f}"
)


# Classify using dynamic threshold
df["dynamic_status"] = df["anomaly_score"].apply(
    lambda score:
        "ANOMALY"
        if score >= dynamic_threshold
        else "NORMAL"
)


# ============================================================
# 8. CONVERT ML PREDICTION TO STATUS
# ============================================================

df["status"] = df["prediction"].map({
    1: "NORMAL",
    -1: "ANOMALY"
})


# ============================================================
# 9. RULE + ML COMBINATION
# ============================================================

print("\nApplying rule-based detection...")

df["rule_anomaly"] = False
df["rule_reasons"] = ""

for index, row in df.iterrows():

    rule_result, reasons = apply_rules(row)

    df.at[index, "rule_anomaly"] = rule_result
    df.at[index, "rule_reasons"] = "; ".join(reasons)


# ============================================================
# 10. FINAL ANOMALY DECISION
# ============================================================

df["final_status"] = "NORMAL"
# ============================================================
# SEVERITY CLASSIFICATION
# ============================================================

def calculate_severity(row):

    if row["final_status"] == "NORMAL":
        return "NORMAL"

    score = row["anomaly_score"]

    # Critical conditions
    if (
        row["failed_login"] == 1 and
        row["auth_activity"] == 1
    ):
        return "CRITICAL"

    if (
        row["timeout_error"] == 1 and
        row["critical_service"] == 1
    ):
        return "CRITICAL"

    # High severity
    if score >= 0.60:
        return "HIGH"

    if row["error_count"] == 1:
        return "HIGH"

    # Medium severity
    if score >= 0.50:
        return "MEDIUM"

    if row["warning_count"] == 1:
        return "MEDIUM"

    # Low severity
    return "LOW"


df["severity"] = df.apply(
    calculate_severity,
    axis=1
)
# ============================================================
# EXPLAINABLE ANOMALY DETECTION
# ============================================================

df["explanation"] = df.apply(
    get_explanation,
    axis=1
)
# ============================================================
# FEATURE CONTRIBUTION
# ============================================================

df["top_features"] = df.apply(
    format_contributions,
    axis=1
)
df.loc[
    (df["status"] == "ANOMALY") |
    (df["rule_anomaly"] == True),
    "final_status"
] = "ANOMALY"
# ============================================================
# SEVERITY CLASSIFICATION
# ============================================================

def calculate_severity(row):

    # Normal event
    if row["final_status"] == "NORMAL":
        return "NORMAL"

    # Critical
    if row["failed_login"] == 1:
        return "CRITICAL"

    if (
        row["timeout_error"] == 1
        and row["critical_service"] == 1
    ):
        return "CRITICAL"

    # High
    if row["error_count"] == 1:
        return "HIGH"

    if row["anomaly_score"] >= 0.60:
        return "HIGH"

    # Medium
    if row["warning_count"] == 1:
        return "MEDIUM"

    if row["anomaly_score"] >= 0.50:
        return "MEDIUM"

    # Low
    return "LOW"


df["severity"] = df.apply(
    calculate_severity,
    axis=1
)


# ============================================================
# 11. DISPLAY RESULTS
# ============================================================

print("\n===== ANOMALY DETECTION RESULTS =====\n")

print(
    df[
        [
            "timestamp",
            "service",
            "level",
            "message",
            "anomaly_score",
            "status",
            "dynamic_status",
            "rule_anomaly",
            "final_status",
            "severity"
        ]
    ].head(20).to_string(index=False)
)


# ============================================================
# 12. DETECTION SUMMARY
# ============================================================

normal_count = (
    df["final_status"] == "NORMAL"
).sum()

anomaly_count = (
    df["final_status"] == "ANOMALY"
).sum()

ml_anomaly_count = (
    df["status"] == "ANOMALY"
).sum()

rule_anomaly_count = (
    df["rule_anomaly"] == True
).sum()


print("\n===== DETECTION SUMMARY =====")

print(f"Total logs          : {len(df)}")
print(f"ML anomalies        : {ml_anomaly_count}")
print(f"Rule anomalies      : {rule_anomaly_count}")
print(f"Final normal logs   : {normal_count}")
print(f"Final anomaly logs  : {anomaly_count}")


# ============================================================
# 13. PREPARE RESULTS FOR MEMBER 3
# ============================================================

results_df = df[
    [
        "timestamp",
        "service",
        "level",
        "message",
        "source_ip",
        "trace_id",
        "anomaly_score",
        "status",
        "rule_anomaly",
        "dynamic_status",
        "rule_reasons",
        "final_status",
        "severity",
        "explanation",
        "top_features"
    ]
].copy()
results_df["timestamp"] = results_df["timestamp"].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)


# ============================================================
# 14. SAVE RESULTS AS JSON
# ============================================================

os.makedirs(
    "ai_detection/output",
    exist_ok=True
)

output_file = (
    "ai_detection/output/anomaly_results.json"
)


# Pandas converts Timestamp into JSON-compatible format
json_data = results_df.to_json(
    orient="records",
    date_format="iso",
    indent=4
)


with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(json_data)


print(
    f"\nResults saved to: {output_file}"
)


# ============================================================
# 15. MODEL EVALUATION
# ============================================================

print("\n===== MODEL EVALUATION =====\n")


# Ground truth:
# NORMAL = 0
# Any abnormal event = 1

df["actual"] = df["ground_truth"].apply(
    lambda x: 0 if x == "NORMAL" else 1
)


# Model prediction:
# NORMAL = 0
# ANOMALY = 1

df["predicted"] = df["prediction"].apply(
    lambda x: 0 if x == 1 else 1
)


# ============================================================
# 16. CLASSIFICATION REPORT
# ============================================================

print(
    classification_report(
        df["actual"],
        df["predicted"],
        target_names=[
            "NORMAL",
            "ANOMALY"
        ],
        zero_division=0
    )
)


# ============================================================
# 17. CONFUSION MATRIX
# ============================================================

print("Confusion Matrix:")

cm = confusion_matrix(
    df["actual"],
    df["predicted"]
)

print(cm)