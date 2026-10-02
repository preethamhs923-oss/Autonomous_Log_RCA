import json
import random
from datetime import datetime, timedelta
import os

TOTAL_LOGS = 2000

services = [
    "auth-service",
    "payment-service",
    "inventory-service",
    "order-service",
    "database-service",
    "api-gateway"
]

normal_messages = [
    "Login successful",
    "Product viewed successfully",
    "Order created successfully",
    "Payment completed successfully",
    "Stock updated successfully",
    "Request processed successfully",
    "User session created",
    "Database query completed"
]

abnormal_events = [
    {
        "type": "BRUTE_FORCE",
        "service": "auth-service",
        "level": "ERROR",
        "message": "Login failed - invalid credentials"
    },
    {
        "type": "DATABASE_TIMEOUT",
        "service": "payment-service",
        "level": "ERROR",
        "message": "Database connection timeout"
    },
    {
        "type": "SERVER_ERROR",
        "service": "api-gateway",
        "level": "ERROR",
        "message": "Internal server error"
    },
    {
        "type": "SERVICE_FAILURE",
        "service": "order-service",
        "level": "ERROR",
        "message": "Service unavailable"
    },
    {
        "type": "CONNECTION_FAILURE",
        "service": "database-service",
        "level": "ERROR",
        "message": "Connection pool exhausted"
    }
]

logs = []

start_time = datetime(2026, 8, 24, 10, 0, 0)

for i in range(TOTAL_LOGS):

    timestamp = start_time + timedelta(
        seconds=random.randint(0, 7200)
    )

    source_ip = f"192.168.1.{random.randint(1, 50)}"

    if random.random() < 0.80:

        service = random.choice(services)

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "service": service,
            "level": "INFO",
            "message": random.choice(normal_messages),
            "source_ip": source_ip,
            "trace_id": f"trace-{i:04d}",
            "ground_truth": "NORMAL"
        }

    else:

        event = random.choice(abnormal_events)

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "service": event["service"],
            "level": event["level"],
            "message": event["message"],
            "source_ip": source_ip,
            "trace_id": f"trace-{i:04d}",
            "ground_truth": event["type"]
        }

    logs.append(log)

os.makedirs("ai_detection/data", exist_ok=True)

output_file = "ai_detection/data/training_logs.json"

with open(output_file, "w") as f:
    json.dump(logs, f, indent=4)

print(f"Generated {len(logs)} logs")
print(f"Dataset saved to: {output_file}")