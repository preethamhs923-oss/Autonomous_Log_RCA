import json


def load_anomaly_results(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def get_anomalies(data):
    anomalies = []

    for record in data:
        if record.get("final_status") == "ANOMALY":
            anomalies.append(record)

    return anomalies


if __name__ == "__main__":

    file_path = "ai_detection/output/anomaly_results.json"

    data = load_anomaly_results(file_path)

    anomalies = get_anomalies(data)

    print("======================================")
    print("       MEMBER 3 - LOG LOADER")
    print("======================================")

    print("Total logs       :", len(data))
    print("Total anomalies  :", len(anomalies))

    if len(anomalies) > 0:

        print("\nFirst anomaly:")
        print("--------------------------------------")

        first = anomalies[0]

        print("Timestamp       :", first.get("timestamp"))
        print("Service         :", first.get("service"))
        print("Level           :", first.get("level"))
        print("Message         :", first.get("message"))
        print("Trace ID        :", first.get("trace_id"))
        print("Anomaly Score   :", first.get("anomaly_score"))
        print("Severity        :", first.get("severity"))
        print("Explanation     :", first.get("explanation"))