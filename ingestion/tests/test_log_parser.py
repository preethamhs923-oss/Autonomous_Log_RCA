from ingestion.parsers.log_parser import parse_log, parse_logs


def test_parse_log():
    raw_log = (
        "2026-08-24 10:30:15 | payment-service | ERROR | "
        "Database connection timeout | 192.168.1.10 | trace-001"
    )

    result = parse_log(raw_log)

    assert result["timestamp"] == "2026-08-24 10:30:15"
    assert result["service"] == "payment-service"
    assert result["level"] == "ERROR"
    assert result["message"] == "Database connection timeout"
    assert result["source_ip"] == "192.168.1.10"
    assert result["trace_id"] == "trace-001"


def test_parse_invalid_log():
    raw_log = "This is an invalid log"

    result = parse_log(raw_log)

    assert result is None


def test_parse_multiple_logs():
    logs = [
        "2026-08-24 10:30:15 | payment-service | ERROR | Database connection timeout | 192.168.1.10 | trace-001",
        "2026-08-24 10:31:20 | payment-service | INFO | Payment request received | 192.168.1.11 | trace-002"
    ]

    results = parse_logs(logs)

    assert len(results) == 2
    assert results[0]["level"] == "ERROR"
    assert results[1]["level"] == "INFO"