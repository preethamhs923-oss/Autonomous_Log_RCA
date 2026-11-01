
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "code_intelligence" / "output"

MAINTAINABILITY_FILE = OUTPUT_DIR / "maintainability_results.json"
COMPLEXITY_FILE = OUTPUT_DIR / "complexity_results.json"
OUTPUT_FILE = OUTPUT_DIR / "technical_debt_results.json"


def load_json(file_path):
    """Load a JSON report if it exists."""
    if not file_path.exists():
        print(f"WARNING: Report not found: {file_path}")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"WARNING: Could not read {file_path.name}: {error}")
        return None


def get_functions(report):
    """Support dictionary-based and list-based analyzer reports."""
    if isinstance(report, list):
        return report

    if isinstance(report, dict):
        for key in ("functions", "results", "function_results"):
            if isinstance(report.get(key), list):
                return report[key]

    return []


def classify_debt(score, issues):
    """Assign priority using the available evidence."""
    text = " ".join(str(issue) for issue in issues).lower()

    if score < 40 or (
        score < 60 and "nesting" in text and "long function" in text
    ):
        return "CRITICAL"

    if score < 60:
        return "HIGH"

    if score < 80:
        return "MEDIUM"

    return "LOW"


def estimate_effort(priority, issues):
    """
    Rough planning estimate, not a measured repair duration.
    """
    base_minutes = {
        "LOW": 15,
        "MEDIUM": 30,
        "HIGH": 60,
        "CRITICAL": 120,
    }

    extra = max(0, len(issues) - 1) * 15
    return base_minutes[priority] + extra


def main():
    maintainability = load_json(MAINTAINABILITY_FILE)
    complexity = load_json(COMPLEXITY_FILE)

    if maintainability is None:
        print(
            "\nRun maintainability_analyzer.py first and "
            "check its output filename."
        )
        return

    maintainability_functions = get_functions(maintainability)
    complexity_functions = get_functions(complexity) if complexity else []

    # Match complexity findings by file and function name.
    complexity_lookup = {}

    for item in complexity_functions:
        name = item.get("name", item.get("function", ""))
        file_name = item.get("file", item.get("filename", ""))
        if name:
            complexity_lookup[(file_name, name)] = item

    debt_items = []

    for item in maintainability_functions:
        name = item.get("name", "")
        file_name = item.get("file", item.get("filename", ""))

        score = item.get("maintainability_score", 100)
        issues = list(item.get("issues", []))

        complexity_item = complexity_lookup.get((file_name, name))

        if complexity_item:
            complexity_value = complexity_item.get(
                "complexity",
                complexity_item.get("cyclomatic_complexity"),
            )

            if isinstance(complexity_value, (int, float)):
                if complexity_value >= 15:
                    issues.append(
                        f"High cyclomatic complexity: {complexity_value}"
                    )
                elif complexity_value >= 10:
                    issues.append(
                        f"Moderate cyclomatic complexity: {complexity_value}"
                    )

        priority = classify_debt(score, issues)

        # Only include functions with reported maintainability or
        # complexity concerns.
        if issues:
            debt_items.append({
                "file": file_name,
                "function": name,
                "start_line": item.get("start_line"),
                "maintainability_score": score,
                "priority": priority,
                "issues": issues,
                "estimated_remediation_minutes": estimate_effort(
                    priority, issues
                ),
                "recommendation": (
                    "Review the findings, add tests, and consider "
                    "small, behavior-preserving refactoring."
                ),
            })

    priority_counts = Counter(
        item["priority"] for item in debt_items
    )

    total_estimated_minutes = sum(
        item["estimated_remediation_minutes"]
        for item in debt_items
    )

    output = {
        "functions_reviewed": len(maintainability_functions),
        "complexity_functions_loaded": len(complexity_functions),
        "technical_debt_items": len(debt_items),
        "priority_summary": {
            priority: priority_counts.get(priority, 0)
            for priority in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        },
        "estimated_total_remediation_minutes": total_estimated_minutes,
        "estimated_total_remediation_hours": round(
            total_estimated_minutes / 60, 2
        ),
        "estimation_note": (
            "Effort estimates are rough planning heuristics, "
            "not measured repair times."
        ),
        "items": sorted(
            debt_items,
            key=lambda item: (
                ["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(
                    item["priority"]
                ),
                item["maintainability_score"],
            ),
        ),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4),
        encoding="utf-8",
    )

    print("===== TECHNICAL DEBT ANALYSIS =====")
    print(f"Functions reviewed : {output['functions_reviewed']}")
    print(f"Debt items found   : {output['technical_debt_items']}")
    print(f"Priority summary   : {output['priority_summary']}")
    print(
        "Estimated effort   : "
        f"{output['estimated_total_remediation_hours']} hours"
    )
    print(f"Results saved to   : {OUTPUT_FILE}")

    if complexity is None:
        print(
            "\nNOTE: Maintainability findings were used without "
            "complexity results."
        )

    print("\nTechnical debt analysis completed.")


if __name__ == "__main__":
    main()
