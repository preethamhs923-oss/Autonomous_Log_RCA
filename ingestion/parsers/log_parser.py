import json
import os


def parse_log(log_line):
    """
    Converts one raw log line into a structured dictionary.
    """

    parts = [part.strip() for part in log_line.split("|")]

    if len(parts) != 6:
        print(f"Skipping invalid log: {log_line}")
        return None

    structured_log = {
        "timestamp": parts[0],
        "service": parts[1],
        "level": parts[2],
        "message": parts[3],
        "source_ip": parts[4],
        "trace_id": parts[5]
    }
    

    return structured_log


def parse_logs(logs):
    """
    Converts multiple raw logs into structured logs.
    """

    structured_logs = []

    for log in logs:
        parsed_log = parse_log(log)

        if parsed_log is not None:
            structured_logs.append(parsed_log)

    return structured_logs


def save_structured_logs(structured_logs, output_path):
    """
    Saves structured logs into a JSON file.
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(structured_logs, file, indent=4)

    print(f"Structured logs saved to: {output_path}")


if __name__ == "__main__":

    sample_logs = [
        "2026-08-24 10:30:15 | payment-service | ERROR | Database connection timeout | 192.168.1.10 | trace-001",
        "2026-08-24 10:31:20 | payment-service | INFO | Payment request received | 192.168.1.11 | trace-002",
        "2026-08-24 10:32:40 | inventory-service | WARNING | Product stock running low | 192.168.1.12 | trace-003",
        "2026-08-24 10:33:45 | payment-service | ERROR | Payment gateway unavailable | 192.168.1.13 | trace-004",
        "2026-08-24 10:34:30 | database-service | ERROR | Database connection timeout | 192.168.1.15 | trace-006",
        "2026-08-24 10:35:00 | inventory-service | INFO | Stock updated successfully | 192.168.1.16 | trace-007",
        "2026-08-24 10:36:12 | payment-service | ERROR | Database connection timeout | 192.168.1.10 | trace-001"
    ]

    structured_logs = parse_logs(sample_logs)

    output_file = "ingestion/output/structured_logs.json"

    save_structured_logs(structured_logs, output_file)

    print("\nStructured logs:")

    for log in structured_logs:
        print(json.dumps(log, indent=4))