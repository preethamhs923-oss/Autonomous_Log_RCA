
import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AST_RESULTS = PROJECT_ROOT / "code_intelligence" / "output" / "ast_results.json"
OUTPUT_FILE = PROJECT_ROOT / "code_intelligence" / "output" / "complexity_results.json"


def calculate_complexity(node):
    """Estimate cyclomatic complexity using common control-flow branches."""
    complexity = 1

    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            complexity += 1
        elif isinstance(child, ast.IfExp):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(0, len(child.values) - 1)
        elif isinstance(child, ast.comprehension):
            complexity += sum(
                1 for condition in child.ifs
            )

    return complexity


def analyze_file(file_path):
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        return [{
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "error": str(exc),
        }]

    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = calculate_complexity(node)

            if complexity <= 5:
                risk = "LOW"
            elif complexity <= 10:
                risk = "MEDIUM"
            else:
                risk = "HIGH"

            results.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "function": node.name,
                "line": node.lineno,
                "complexity": complexity,
                "risk": risk,
            })

    return results


def main():
    if not AST_RESULTS.exists():
        raise FileNotFoundError(
            f"AST results not found: {AST_RESULTS}. "
            "Run ast_parser.py first."
        )

    # Use the AST parser's file inventory.
    ast_data = json.loads(AST_RESULTS.read_text(encoding="utf-8"))
    all_results = []

    for item in ast_data:
        if item.get("status") != "success":
            continue

        file_path = PROJECT_ROOT / item["file"]
        if file_path.exists():
            all_results.extend(analyze_file(file_path))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(all_results, indent=4),
        encoding="utf-8",
    )

    function_results = [
        item for item in all_results if "complexity" in item
    ]
    high_risk = sum(
        item["risk"] == "HIGH" for item in function_results
    )
    medium_risk = sum(
        item["risk"] == "MEDIUM" for item in function_results
    )
    low_risk = sum(
        item["risk"] == "LOW" for item in function_results
    )

    print("===== COMPLEXITY ANALYSIS =====")
    print(f"Functions analyzed : {len(function_results)}")
    print(f"Low risk           : {low_risk}")
    print(f"Medium risk        : {medium_risk}")
    print(f"High risk          : {high_risk}")
    print(f"Results saved to   : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
