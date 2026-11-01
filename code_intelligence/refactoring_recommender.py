
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"

INPUT_FILES = {
    "complexity": "complexity_results.json",
    "maintainability": "maintainability_results.json",
    "technical_debt": "technical_debt_results.json",
    "duplicate_logic": "duplicate_logic_results.json",
    "semantic": "semantic_analysis_results.json",
}

OUTPUT_FILE = OUTPUT_DIR / "refactoring_recommendations.json"


def load_json(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        print(f"WARNING: Missing {filename}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"WARNING: Could not read {filename}: {error}")
        return None


def find_records(data):
    """Extract record lists from common JSON output structures."""
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in (
            "results", "findings", "functions",
            "recommendations", "matches", "items"
        ):
            value = data.get(key)
            if isinstance(value, list):
                return value

    return []


def recommend_from_record(source, record):
    """Create a recommendation from a finding."""
    if not isinstance(record, dict):
        return None

    text = " ".join(
        str(record.get(key, ""))
        for key in (
            "issues", "issue", "message", "description",
            "name", "function", "function_name", "risk",
            "priority", "pattern", "classification"
        )
    ).lower()

    file_name = (
        record.get("file")
        or record.get("filename")
        or record.get("path")
        or "Unknown file"
    )

    function_name = (
        record.get("name")
        or record.get("function")
        or record.get("function_name")
        or "Review finding"
    )

    if source == "complexity":
        action = "Review control flow and simplify complex functions."
    elif source == "maintainability":
        action = "Improve readability, reduce nesting, and split long functions where appropriate."
    elif source == "technical_debt":
        action = "Review the debt finding and prioritize a safe, tested fix."
    elif source == "duplicate_logic":
        action = "Check whether the repeated logic can be extracted into a shared function."
    else:
        action = "Compare the functions manually before considering shared implementation."

    priority = "MEDIUM"

    if any(word in text for word in ("critical", "very high", "high risk")):
        priority = "HIGH"

    if any(word in text for word in ("low risk", "minor")):
        priority = "LOW"

    return {
        "source": source,
        "file": str(file_name),
        "function": str(function_name),
        "priority": priority,
        "finding": text[:500] or "Review the analyzer finding.",
        "recommendation": action,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    recommendations = []
    loaded_count = 0

    for source, filename in INPUT_FILES.items():
        data = load_json(filename)

        if data is None:
            continue

        loaded_count += 1

        for record in find_records(data):
            item = recommend_from_record(source, record)

            if item:
                recommendations.append(item)

    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(
        key=lambda item: priority_order[item["priority"]]
    )

    result = {
        "analyzers_loaded": loaded_count,
        "recommendation_count": len(recommendations),
        "priority_summary": {
            priority: sum(
                item["priority"] == priority
                for item in recommendations
            )
            for priority in ("HIGH", "MEDIUM", "LOW")
        },
        "recommendations": recommendations,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print("\n===== REFACTORING RECOMMENDATIONS =====")
    print(f"Analyzers loaded       : {loaded_count}")
    print(f"Recommendations found  : {len(recommendations)}")
    print(f"Priority summary       : {result['priority_summary']}")
    print(f"Results saved to       : {OUTPUT_FILE}")
    print("\nRefactoring recommendation analysis completed.")


if __name__ == "__main__":
    main()
