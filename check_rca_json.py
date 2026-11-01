
import json
from pathlib import Path

root = Path(__file__).resolve().parent

files = {
    "incidents": root / "rca_engine" / "incident_results.json",
    "incident_intelligence": root / "rca_engine" / "incident_intelligence_results.json",
    "root_causes": root / "rca_engine" / "root_cause_results.json",
}

for name, path in files.items():
    print(f"\n--- {name} ---")

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        print("Type: list")
        print("Count:", len(data))
        if data:
            print("First record keys:", list(data[0].keys()) if isinstance(data[0], dict) else type(data[0]).__name__)
            print(json.dumps(data[0], indent=2, default=str)[:800])
    elif isinstance(data, dict):
        print("Type: dict")
        print("Keys:", list(data.keys()))
        for key, value in data.items():
            if isinstance(value, list):
                print(f"{key}: {len(value)} items")
        print(json.dumps(data, indent=2, default=str)[:800])
    else:
        print("Unexpected type:", type(data).__name__)
