from app.services import anomaly_detection, booking_manual, duplicate_detection


def test_anomaly_detection_empty():
    assert anomaly_detection.detect([]) == []


def test_duplicate_detection_empty():
    assert duplicate_detection.detect([]) == []


def test_booking_manual_empty():
    assert booking_manual.derive_rules([]) == []
