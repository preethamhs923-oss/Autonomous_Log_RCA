
import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}

def parse_python_file(file_path):
    """Extract structural information from one Python file."""

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "arguments": len(node.args.args),
                    "is_async": isinstance(
                        node, ast.AsyncFunctionDef
                    ),
                })

            elif isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": [
                        item.name
                        for item in node.body
                        if isinstance(
                            item,
                            (ast.FunctionDef, ast.AsyncFunctionDef)
                        )
                    ],
                })

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")

        return {
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "status": "success",
            "functions": functions,
            "classes": classes,
            "imports": sorted(set(imports)),
        }

    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        return {
            "file": str(file_path),
            "status": "error",
            "error": str(exc),
            "functions": [],
            "classes": [],
            "imports": [],
        }


def scan_project():
    """Scan project Python files, excluding generated/vendor folders."""

    results = []

    for file_path in PROJECT_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in file_path.parts):
            continue

        results.append(parse_python_file(file_path))

    return results


def main():
    results = scan_project()

    output_dir = PROJECT_ROOT / "code_intelligence" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "ast_results.json"
    output_file.write_text(
        json.dumps(results, indent=4),
        encoding="utf-8",
    )

    successful = sum(
        result["status"] == "success"
        for result in results
    )
    failed = len(results) - successful

    print("===== AST PARSER RESULTS =====")
    print(f"Python files scanned : {len(results)}")
    print(f"Successful parses    : {successful}")
    print(f"Failed parses        : {failed}")
    print(f"Results saved to     : {output_file}")


if __name__ == "__main__":
    main()
