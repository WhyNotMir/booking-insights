import json
from pathlib import Path

from app.services import anomaly_detection, booking_manual, duplicate_detection

DATA_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "journal_entries.json"


def test_anomaly_detection_empty():
    assert anomaly_detection.detect([]) == []


def test_duplicate_detection_empty():
    assert duplicate_detection.detect([]) == []


def test_booking_manual_empty():
    assert booking_manual.derive_rules([]) == []


def test_anomaly_detection_finds_planted_text_variants():
    entries = json.loads(DATA_PATH.read_text())
    findings = anomaly_detection.detect(entries)
    reasons = " ".join(finding["reason"] for finding in findings)

    assert "Sofware Subscription" in reasons
    assert "Maintenence Invoice" in reasons
    assert "Office Supply Invoice" in reasons


def test_anomaly_detection_finds_unusual_account_text_combo():
    entries = json.loads(DATA_PATH.read_text())
    findings = anomaly_detection.detect(entries)

    assert any(
        finding["type"] == "account_text_combo"
        and "Room Revenue" in finding["reason"]
        and "580000" in finding["reason"]
        for finding in findings
    )


def test_booking_manual_derives_core_rule_types():
    entries = json.loads(DATA_PATH.read_text())
    rules = booking_manual.derive_rules(entries)
    rule_types = {rule["type"] for rule in rules}

    assert "account_tax" in rule_types
    assert "account_cost_center" in rule_types
    assert "recurring_text_account" in rule_types


def test_booking_manual_rules_include_evidence_and_validation_check():
    entries = json.loads(DATA_PATH.read_text())
    rules = booking_manual.derive_rules(entries)

    assert rules
    assert all(rule["validation_check"] for rule in rules)
    assert all(rule["evidence_count"] >= 5 for rule in rules)
    assert all(rule["evidence_examples"] for rule in rules)


def test_duplicate_detection_finds_planted_documents():
    entries = json.loads(DATA_PATH.read_text())
    findings = duplicate_detection.detect(entries)

    flagged_documents = {
        line["document_id"]
        for finding in findings
        for line in finding["lines"]
    }

    for planted in ("DOC9991", "DOC9992", "DOC9993"):
        assert planted in flagged_documents, f"Missing planted duplicate {planted}"


def test_duplicate_detection_returns_document_level_clusters():
    entries = json.loads(DATA_PATH.read_text())
    findings = duplicate_detection.detect(entries)

    assert findings, "Expected at least one duplicate finding"
    for finding in findings:
        assert finding["type"] == "duplicate_document"
        assert 0 <= finding["confidence"] <= 1
        assert finding["evidence_count"] >= 1
        assert finding["criteria"]
        document_ids = {line["document_id"] for line in finding["lines"]}
        assert len(document_ids) == 2, "Cluster must span exactly two documents"


def test_duplicate_findings_sorted_by_confidence_desc():
    entries = json.loads(DATA_PATH.read_text())
    findings = duplicate_detection.detect(entries)
    confidences = [finding["confidence"] for finding in findings]
    assert confidences == sorted(confidences, reverse=True)
