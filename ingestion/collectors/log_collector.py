import os


def collect_logs(file_path):
    """
    Reads raw logs from the given file
    and returns them as a list.
    """

    if not os.path.exists(file_path):
        print(f"Log file not found: {file_path}")
        return []

    collected_logs = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                collected_logs.append(line)

    return collected_logs


if __name__ == "__main__":
    log_file_path = "ingestion/logs/sample_logs.txt"

    logs = collect_logs(log_file_path)

    print("Number of logs collected:", len(logs))

    print("\nCollected logs:")

    for log in logs:
        print(log)