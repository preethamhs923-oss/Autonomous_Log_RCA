
import json
from pathlib import Path

files = [
    "rca_engine/incident_results.json",
    "rca_engine/incident_intelligence_results.json",
    "rca_engine/pattern_results.json",
    "rca_engine/root_cause_results.json",
    "code_intelligence/output/code_intelligence_report.json",
    "code_intelligence/output/refactoring_recommendations.json",
]

for filename in files:
    path = Path(filename)
    print(f"\n{'=' * 60}")
    print(f"FILE: {filename}")

    if not path.exists():
        print("NOT FOUND")
        continue

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print(f"READ ERROR: {error}")
        continue

    print("Type:", type(data).__name__)

    if isinstance(data, list):
        print("Record count:", len(data))
        if data:
            print("First record:")
            print(json.dumps(data[0], indent=2, default=str)[:2000])

    elif isinstance(data, dict):
        print("Keys:", list(data.keys()))
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                print(f"  {key}: {type(value).__name__}, {len(value)} items")
            else:
                print(f"  {key}: {type(value).__name__}")

        for key, value in data.items():
            if isinstance(value, list) and value:
                print(f"First item in '{key}':")
                print(json.dumps(value[0], indent=2, default=str)[:1500])
                break
