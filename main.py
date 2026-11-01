
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_module(module_path, module_name, optional=False):
    full_path = PROJECT_ROOT / module_path

    print("\n" + "=" * 70)
    print(f"RUNNING: {module_name}")
    print("=" * 70)

    if not full_path.exists():
        message = f"Module not found: {full_path}"

        if optional:
            print(f"WARNING: {message}")
            print("Skipping this optional module.")
            return False

        print(f"\nERROR: {message}")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(full_path)],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        if optional:
            print(f"\nWARNING: {module_name} failed.")
            print("Continuing with the remaining optional modules.")
            return False

        print(f"\nERROR: {module_name} failed.")
        print("Pipeline stopped.")
        sys.exit(result.returncode)

    print(f"\n{module_name} completed successfully.")
    return True


def main():
    print("=" * 70)
    print("        AUTONOMOUS LOG ROOT CAUSE ANALYSIS")
    print("              END-TO-END PIPELINE")
    print("=" * 70)

    # ==============================================================
    # PART 1: EXISTING RCA PIPELINE
    # ==============================================================

    rca_modules = [
        ("anomaly_detection.py", "AI ANOMALY DETECTION"),
        ("rca_engine/event_correlation.py", "EVENT CORRELATION"),
        ("rca_engine/pattern_detector.py", "PATTERN DETECTION"),
        ("rca_engine/incident_clustering.py", "INCIDENT CLUSTERING"),
        ("rca_engine/root_cause_engine.py", "ROOT CAUSE ANALYSIS"),
        ("rca_engine/incident_intelligence.py", "INCIDENT INTELLIGENCE"),
    ]

    for module_path, module_name in rca_modules:
        run_module(module_path, module_name)

    # ==============================================================
    # PART 2: CODE INTELLIGENCE ANALYSIS
    # ==============================================================

    code_modules = [
        (
            "code_intelligence/ast_parser.py",
            "AST PARSING"
        ),
        (
            "code_intelligence/complexity_analyzer.py",
            "COMPLEXITY ANALYSIS"
        ),
        (
            "code_intelligence/dead_code_detector.py",
            "DEAD CODE DETECTION"
        ),
        (
            "code_intelligence/duplicate_logic_detector.py",
            "DUPLICATE LOGIC DETECTION"
        ),
        (
            "code_intelligence/maintainability_analyzer.py",
            "MAINTAINABILITY ANALYSIS"
        ),
        (
            "code_intelligence/technical_debt_analyzer.py",
            "TECHNICAL DEBT ANALYSIS"
        ),
        (
            "code_intelligence/semantic_analyzer.py",
            "SEMANTIC ANALYSIS"
        ),
        (
            "code_intelligence/refactoring_recommender.py",
            "REFACTORING RECOMMENDATIONS"
        ),
        (
            "code_intelligence/code_intelligence_report.py",
            "CODE INTELLIGENCE REPORT"
        ),
    ]

    for module_path, module_name in code_modules:
        run_module(module_path, module_name, optional=True)

    # ==============================================================
    # PART 3: COMPLETION SUMMARY
    # ==============================================================

    print("\n" + "=" * 70)
    print("                 PIPELINE COMPLETED")
    print("=" * 70)

    print("\nRCA Results:")
    print("1. ai_detection/output/anomaly_results.json")
    print("2. rca_engine/pattern_results.json")
    print("3. rca_engine/incident_results.json")
    print("4. rca_engine/root_cause_results.json")
    print("5. rca_engine/incident_intelligence_results.json")

    print("\nCode Intelligence Results:")
    print("1. code_intelligence/output/ast_results.json")
    print("2. code_intelligence/output/complexity_results.json")
    print("3. code_intelligence/output/dead_code_results.json")
    print("4. code_intelligence/output/duplicate_logic_results.json")
    print("5. code_intelligence/output/maintainability_results.json")
    print("6. code_intelligence/output/technical_debt_results.json")
    print("7. code_intelligence/output/semantic_analysis_results.json")
    print("8. code_intelligence/output/refactoring_recommendations.json")
    print("9. code_intelligence/output/code_intelligence_report.json")

    print("\nAutonomous Log RCA and Code Intelligence pipeline finished.")


if __name__ == "__main__":
    main()
