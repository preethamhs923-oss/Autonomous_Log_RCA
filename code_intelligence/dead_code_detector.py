
import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "code_intelligence" / "output"
OUTPUT_FILE = OUTPUT_DIR / "dead_code_results.json"

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}


def scan_python_files():
    """Parse Python files and collect definitions and references."""

    definitions = []
    references = []

    for path in PROJECT_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        relative_path = str(path.relative_to(PROJECT_ROOT))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ignore common special methods for this first pass.
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                definitions.append({
                    "name": node.name,
                    "kind": "function",
                    "file": relative_path,
                    "line": node.lineno,
                })

            elif isinstance(node, ast.ClassDef):
                definitions.append({
                    "name": node.name,
                    "kind": "class",
                    "file": relative_path,
                    "line": node.lineno,
                })

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                references.append(node.id)

            elif isinstance(node, ast.Call):
                # Catch calls such as package.function(...)
                if isinstance(node.func, ast.Attribute):
                    references.append(node.func.attr)

    return definitions, references


def main():
    definitions, references = scan_python_files()
    reference_set = set(references)

    findings = []

    for item in definitions:
        if item["name"] not in reference_set:
            findings.append({
                **item,
                "status": "POTENTIALLY_UNUSED",
                "note": (
                    "No matching name reference was found in scanned Python "
                    "files. Verify dynamic calls, framework usage, entry points, "
                    "and external references before deciding this is dead code."
                ),
            })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(findings, indent=4),
        encoding="utf-8",
    )

    print("===== POTENTIAL DEAD CODE ANALYSIS =====")
    print(f"Definitions scanned       : {len(definitions)}")
    print(f"Potentially unused items  : {len(findings)}")
    print(f"Results saved to          : {OUTPUT_FILE}")
    print("Review each finding before removing any code.")


if __name__ == "__main__":
    main()
