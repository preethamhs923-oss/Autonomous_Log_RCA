import json
from kafka import KafkaProducer


def create_producer():
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda value: json.dumps(value).encode("utf-8")
    )

    return producer


def send_logs_to_kafka(logs):
    producer = create_producer()

    topic_name = "structured-logs"

    for log in logs:
        producer.send(topic_name, value=log)

    producer.flush()

    print(f"{len(logs)} logs sent successfully to Kafka topic: {topic_name}")


if __name__ == "__main__":
    with open(
        "ingestion/output/structured_logs.json",
        "r",
        encoding="utf-8"
    ) as file:
        structured_logs = json.load(file)

    send_logs_to_kafka(structured_logs)