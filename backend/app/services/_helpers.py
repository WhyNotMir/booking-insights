"""Shared helpers for detection services.

Centralises the shape of journal-line samples that every finding type
embeds (`affected_lines`, `evidence_examples`, duplicate `lines`). Keeping
one definition here means the frontend's `JournalLineSample` interface has
a single backend source of truth instead of three subtly-different copies.
"""


def line_id(entry: dict) -> str:
    """Stable identifier for a single journal line: 'DOCxxxx/N'."""
    return f"{entry['document_id']}/{entry['line_id']}"


def line_sample(entry: dict) -> dict:
    """Full sample of a journal line for embedding in findings.

    Includes every field the frontend's JournalLineSample type cares about
    so the same renderer can be used across anomaly, duplicate, and rule
    findings.
    """
    return {
        "document_id": entry["document_id"],
        "line_id": entry["line_id"],
        "posting_date": entry["posting_date"],
        "gl_account": entry["gl_account"],
        "cost_center": entry.get("cost_center", ""),
        "amount": entry["amount"],
        "currency": entry["currency"],
        "debit_credit": entry["debit_credit"],
        "booking_text": entry["booking_text"],
        "vendor_id": entry.get("vendor_id", ""),
        "customer_id": entry.get("customer_id", ""),
        "tax_code": entry.get("tax_code", ""),
    }
