import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_module(module_path, module_name):
    print("\n" + "=" * 70)
    print(f"RUNNING: {module_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / module_path)],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print(f"\nERROR: {module_name} failed.")
        print("Pipeline stopped.")
        sys.exit(result.returncode)

    print(f"\n{module_name} completed successfully.")


def main():

    print("=" * 70)
    print("        AUTONOMOUS LOG ROOT CAUSE ANALYSIS")
    print("              END-TO-END PIPELINE")
    print("=" * 70)

    # Step 1 - AI Anomaly Detection
    run_module(
        "anomaly_detection.py",
        "AI ANOMALY DETECTION"
    )

    # Step 2 - Event Correlation
    run_module(
        "rca_engine/event_correlation.py",
        "EVENT CORRELATION"
    )

    # Step 3 - Pattern Detection
    run_module(
        "rca_engine/pattern_detector.py",
        "PATTERN DETECTION"
    )

    # Step 4 - Incident Clustering
    run_module(
        "rca_engine/incident_clustering.py",
        "INCIDENT CLUSTERING"
    )

    # Step 5 - Root Cause Analysis
    run_module(
        "rca_engine/root_cause_engine.py",
        "ROOT CAUSE ANALYSIS"
    )

    # Step 6 - Incident Intelligence
    run_module(
        "rca_engine/incident_intelligence.py",
        "INCIDENT INTELLIGENCE"
    )

    print("\n" + "=" * 70)
    print("             PIPELINE COMPLETED")
    print("=" * 70)

    print("\nGenerated Results:")
    print("1. ai_detection/output/anomaly_results.json")
    print("2. rca_engine/pattern_results.json")
    print("3. rca_engine/incident_results.json")
    print("4. rca_engine/root_cause_results.json")
    print("5. rca_engine/incident_intelligence_results.json")

    print("\nAutonomous Log RCA pipeline completed successfully.")


if __name__ == "__main__":
    main()