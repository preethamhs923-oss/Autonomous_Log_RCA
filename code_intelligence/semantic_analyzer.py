
import ast
import json
import re
import tokenize
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from io import StringIO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "code_intelligence" / "output"
OUTPUT_FILE = OUTPUT_DIR / "semantic_analysis_results.json"

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
}

MIN_FUNCTION_LINES = 5
SIMILARITY_THRESHOLD = 0.65


def tokenize_function(source):
    """Extract meaningful Python tokens while ignoring comments."""
    tokens = []

    try:
        for token in tokenize.generate_tokens(StringIO(source).readline):
            if token.type in {
                tokenize.NAME,
                tokenize.OP,
                tokenize.NUMBER,
                tokenize.STRING,
            }:
                value = token.string

                # Normalize identifiers and literal values so functions
                # using different variable names can still be compared.
                if token.type == tokenize.NAME:
                    value = value.lower()
                elif token.type == tokenize.NUMBER:
                    value = "<number>"
                elif token.type == tokenize.STRING:
                    value = "<string>"

                tokens.append(value)

    except (tokenize.TokenError, IndentationError):
        return []

    return tokens


def extract_functions():
    functions = []
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
        lines = source.splitlines()
        relative_path = str(path.relative_to(PROJECT_ROOT))

        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue

            start = node.lineno
            end = getattr(node, "end_lineno", start)
            line_count = end - start + 1

            if line_count < MIN_FUNCTION_LINES:
                continue

            function_source = "\n".join(lines[start - 1:end])
            tokens = tokenize_function(function_source)

            if not tokens:
                continue

            # Collect function calls and identifiers as additional signals.
            calls = sorted({
                child.func.id
                if isinstance(child.func, ast.Name)
                else child.func.attr
                if isinstance(child.func, ast.Attribute)
                else ""
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
            } - {""})

            identifiers = sorted({
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name)
            })

            functions.append({
                "name": node.name,
                "file": relative_path,
                "start_line": start,
                "end_line": end,
                "lines": line_count,
                "tokens": tokens,
                "calls": calls,
                "identifiers": identifiers,
            })

    return functions, files_scanned, failed_files


def similarity(first, second):
    """Compare normalized code and supporting structural signals."""
    token_similarity = SequenceMatcher(
        None, first["tokens"], second["tokens"]
    ).ratio()

    first_calls = set(first["calls"])
    second_calls = set(second["calls"])
    call_union = first_calls | second_calls

    if call_union:
        call_similarity = len(first_calls & second_calls) / len(call_union)
    else:
        call_similarity = 0.0

    first_names = set(first["identifiers"])
    second_names = set(second["identifiers"])
    name_union = first_names | second_names

    if name_union:
        identifier_similarity = (
            len(first_names & second_names) / len(name_union)
        )
    else:
        identifier_similarity = 0.0

    # Token structure is the main signal; calls and identifiers
    # provide supporting evidence.
    score = (
        0.70 * token_similarity
        + 0.20 * call_similarity
        + 0.10 * identifier_similarity
    )

    return round(score, 4)


def main():
    functions, files_scanned, failed_files = extract_functions()
    matches = []

    # Avoid comparing a function against itself or against another
    # definition in the same file.
    for first, second in combinations(functions, 2):
        if first["file"] == second["file"]:
            continue

        score = similarity(first, second)

        if score >= SIMILARITY_THRESHOLD:
            matches.append({
                "similarity": score,
                "classification": (
                    "HIGH_SIMILARITY"
                    if score >= 0.85
                    else "POTENTIAL_SIMILARITY"
                ),
                "function_1": {
                    "name": first["name"],
                    "file": first["file"],
                    "start_line": first["start_line"],
                    "end_line": first["end_line"],
                },
                "function_2": {
                    "name": second["name"],
                    "file": second["file"],
                    "start_line": second["start_line"],
                    "end_line": second["end_line"],
                },
                "recommendation": (
                    "Review both functions to determine whether they "
                    "implement the same responsibility. Similarity "
                    "alone does not prove duplicate logic."
                ),
            })

    matches.sort(key=lambda item: item["similarity"], reverse=True)

    output = {
        "python_files_scanned": files_scanned,
        "failed_files": failed_files,
        "functions_compared": len(functions),
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "matches_found": len(matches),
        "methodology": (
            "Heuristic similarity using normalized tokens, function "
            "calls, and identifiers. This is not an embedding-based "
            "or LLM-based semantic understanding system."
        ),
        "matches": matches,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4),
        encoding="utf-8",
    )

    print("===== SEMANTIC CODE ANALYSIS =====")
    print(f"Python files scanned : {files_scanned}")
    print(f"Failed files         : {failed_files}")
    print(f"Functions compared   : {len(functions)}")
    print(f"Similarity threshold : {SIMILARITY_THRESHOLD}")
    print(f"Potential matches    : {len(matches)}")
    print(f"Results saved to     : {OUTPUT_FILE}")

    for match in matches[:10]:
        first = match["function_1"]
        second = match["function_2"]

        print(
            f"\nSimilarity: {match['similarity']:.2%} "
            f"({match['classification']})"
        )
        print(
            f"  {first['file']}:{first['start_line']} "
            f"- {first['name']}"
        )
        print(
            f"  {second['file']}:{second['start_line']} "
            f"- {second['name']}"
        )

    print("\nSemantic analysis completed.")


if __name__ == "__main__":
    main()
