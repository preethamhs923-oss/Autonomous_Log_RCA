
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"

INPUT_FILES = [
    "ast_results.json",
    "complexity_results.json",
    "dead_code_results.json",
    "duplicate_logic_results.json",
    "maintainability_results.json",
    "technical_debt_results.json",
    "semantic_analysis_results.json",
    "refactoring_recommendations.json",
]

REPORT_FILE = OUTPUT_DIR / "code_intelligence_report.json"


def load_json(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"WARNING: Could not read {filename}: {error}")
        return None


def summarize(data):
    """Extract a useful summary without assuming one JSON schema."""
    if isinstance(data, list):
        return {
            "record_count": len(data),
            "top_level_keys": [],
        }

    if not isinstance(data, dict):
        return {
            "record_count": 0,
            "top_level_keys": [],
        }

    record_count = 0

    for key in (
        "results", "findings", "functions", "items",
        "matches", "recommendations", "files"
    ):
        value = data.get(key)
        if isinstance(value, list):
            record_count = len(value)
            break

    return {
        "record_count": record_count,
        "top_level_keys": list(data.keys()),
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    analyzers = {}
    missing_files = []

    for filename in INPUT_FILES:
        data = load_json(filename)

        if data is None:
            missing_files.append(filename)
            continue

        analyzers[filename] = summarize(data)

    recommendation_data = load_json("refactoring_recommendations.json")
    recommendations = []

    if isinstance(recommendation_data, dict):
        items = recommendation_data.get("recommendations", [])
        if isinstance(items, list):
            recommendations = items

    priority_summary = {
        priority: sum(
            1 for item in recommendations
            if isinstance(item, dict)
            and str(item.get("priority", "")).upper() == priority
        )
        for priority in ("HIGH", "MEDIUM", "LOW")
    }

    report = {
        "report_title": "Autonomous Log RCA - Code Intelligence Report",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "analyzers_loaded": len(analyzers),
        "analyzer_summaries": analyzers,
        "missing_files": missing_files,
        "recommendation_count": len(recommendations),
        "priority_summary": priority_summary,
        "recommendations": recommendations,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n===== CODE INTELLIGENCE REPORT =====")
    print(f"Analyzers loaded      : {len(analyzers)}")
    print(f"Missing result files  : {len(missing_files)}")
    print(f"Recommendations      : {len(recommendations)}")
    print(f"Priority summary     : {priority_summary}")

    if missing_files:
        print("\nMissing files:")
        for filename in missing_files:
            print(f" - {filename}")

    print(f"\nReport saved to: {REPORT_FILE}")
    print("Code Intelligence reporting completed.")


if __name__ == "__main__":
    main()
