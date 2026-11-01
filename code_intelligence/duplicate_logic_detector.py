
import ast
import hashlib
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "code_intelligence" / "output"
OUTPUT_FILE = OUTPUT_DIR / "duplicate_logic_results.json"

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
}


def normalize_node(node):
    """Normalize an AST node to compare code structure."""
    return ast.dump(node, include_attributes=False)


def scan_for_duplicates():
    blocks = defaultdict(list)
    files_scanned = 0

    for path in PROJECT_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        files_scanned += 1
        relative_path = str(path.relative_to(PROJECT_ROOT))

        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue

            # Ignore tiny blocks; they are often naturally similar.
            if len(node.body) < 4:
                continue

            normalized = normalize_node(node)
            fingerprint = hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest()

            blocks[fingerprint].append({
                "name": node.name,
                "file": relative_path,
                "line": node.lineno,
                "type": type(node).__name__,
                "lines": getattr(node, "end_lineno", node.lineno)
                         - node.lineno + 1,
            })

    duplicates = []

    for fingerprint, locations in blocks.items():
        if len(locations) > 1:
            duplicates.append({
                "fingerprint": fingerprint,
                "occurrences": len(locations),
                "locations": locations,
                "status": "POTENTIAL_DUPLICATE",
                "note": (
                    "Identical normalized syntax was found. "
                    "Review before refactoring."
                ),
            })

    return files_scanned, duplicates


def main():
    files_scanned, duplicates = scan_for_duplicates()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(duplicates, indent=4),
        encoding="utf-8",
    )

    print("===== DUPLICATE LOGIC ANALYSIS =====")
    print(f"Python files scanned : {files_scanned}")
    print(f"Duplicate groups     : {len(duplicates)}")
    print(f"Results saved to     : {OUTPUT_FILE}")

    if not duplicates:
        print(
            "No identical function/class blocks found. "
            "This does not rule out partial or semantic duplication."
        )
    else:
        for index, group in enumerate(duplicates, start=1):
            print(f"\nGroup {index}: {group['occurrences']} occurrences")
            for location in group["locations"]:
                print(
                    f"  {location['file']}:{location['line']} "
                    f"- {location['name']}"
                )


if __name__ == "__main__":
    main()
