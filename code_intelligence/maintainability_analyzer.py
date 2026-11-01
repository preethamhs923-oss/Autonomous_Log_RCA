
import ast
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "code_intelligence" / "output"
OUTPUT_FILE = OUTPUT_DIR / "maintainability_results.json"

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}


def analyze_function(node, relative_path):
    """Analyze function length, parameters, and nesting."""

    start_line = node.lineno
    end_line = getattr(node, "end_lineno", start_line)
    function_length = end_line - start_line + 1

    parameters = (
        node.args.posonlyargs
        + node.args.args
        + node.args.kwonlyargs
    )

    # Exclude self and cls from the parameter count.
    parameter_count = len(parameters)
    if parameters and parameters[0].arg in {"self", "cls"}:
        parameter_count -= 1

    max_nesting = 0

    def visit_nested(child, depth=0):
        nonlocal max_nesting

        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.With,
                ast.AsyncWith,
                ast.Try,
                ast.ExceptHandler,
            ),
        ):
            depth += 1
            max_nesting = max(max_nesting, depth)

        for descendant in ast.iter_child_nodes(child):
            visit_nested(descendant, depth)

    for statement in node.body:
        visit_nested(statement)

    issues = []

    if function_length > 50:
        issues.append("Long function: more than 50 lines")

    if parameter_count > 5:
        issues.append("Too many parameters: more than 5")

    if max_nesting > 3:
        issues.append("Deep nesting: more than 3 levels")

    # A simple heuristic, not a formal maintainability index.
    penalty = (
        max(0, function_length - 30) * 0.5
        + max(0, parameter_count - 4) * 3
        + max(0, max_nesting - 2) * 5
    )

    score = max(0, round(100 - penalty, 2))

    if score >= 80:
        risk = "LOW"
    elif score >= 60:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return {
        "name": node.name,
        "file": relative_path,
        "start_line": start_line,
        "end_line": end_line,
        "lines": function_length,
        "parameter_count": parameter_count,
        "max_nesting": max_nesting,
        "maintainability_score": score,
        "risk": risk,
        "issues": issues,
    }


def main():
    results = []
    files_scanned = 0
    failed_files = 0

    for path in PROJECT_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            failed_files += 1
            continue

        files_scanned += 1
        relative_path = str(path.relative_to(PROJECT_ROOT))

        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                results.append(analyze_function(node, relative_path))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "files_scanned": files_scanned,
        "failed_files": failed_files,
        "functions_analyzed": len(results),
        "risk_summary": {
            "low": sum(r["risk"] == "LOW" for r in results),
            "medium": sum(r["risk"] == "MEDIUM" for r in results),
            "high": sum(r["risk"] == "HIGH" for r in results),
        },
        "functions": results,
        "methodology": (
            "Heuristic score based on function length, parameter "
            "count, and nesting depth. It is not a formal "
            "maintainability index."
        ),
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4),
        encoding="utf-8",
    )

    print("===== MAINTAINABILITY ANALYSIS =====")
    print(f"Python files scanned : {files_scanned}")
    print(f"Failed files         : {failed_files}")
    print(f"Functions analyzed   : {len(results)}")
    print(f"Low risk             : {output['risk_summary']['low']}")
    print(f"Medium risk          : {output['risk_summary']['medium']}")
    print(f"High risk            : {output['risk_summary']['high']}")
    print(f"Results saved to     : {OUTPUT_FILE}")

    print("\nTOP 10 FUNCTIONS TO REVIEW")
    flagged = sorted(
        (r for r in results if r["issues"]),
        key=lambda r: r["maintainability_score"],
    )

    for item in flagged[:10]:
        print(
            f"{item['file']}:{item['start_line']} "
            f"{item['name']} | Score: "
            f"{item['maintainability_score']} | "
            f"Issues: {', '.join(item['issues'])}"
        )

    print("\nMaintainability analysis completed.")


if __name__ == "__main__":
    main()
