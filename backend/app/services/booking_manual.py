"""Derive lightweight booking rule suggestions from journal history."""

from collections import Counter, defaultdict

MIN_EVIDENCE_COUNT = 5
MIN_CONFIDENCE = 0.75
MAX_RULES_PER_KIND = 6
MAX_TOTAL_RULES = 10


def _line_id(entry: dict) -> str:
    return f"{entry['document_id']}/{entry['line_id']}"


def _line_sample(entry: dict) -> dict:
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


def _examples(entries: list[dict], predicate, limit: int = 3) -> list[dict]:
    return [_line_sample(entry) for entry in entries if predicate(entry)][:limit]


def _dominant_rules(
    entries: list[dict],
    group_field: str,
    value_field: str,
    rule_type: str,
    title_template: str,
    check_template: str,
) -> list[dict]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        group_value = entry.get(group_field)
        value = entry.get(value_field)
        if not group_value or not value:
            continue
        grouped[group_value][value] += 1

    rules = []
    for group_value, counts in grouped.items():
        total = sum(counts.values())
        if total < MIN_EVIDENCE_COUNT:
            continue

        expected_value, evidence_count = counts.most_common(1)[0]
        confidence = evidence_count / total
        if confidence < MIN_CONFIDENCE:
            continue

        rules.append({
            "type": rule_type,
            "title": title_template.format(group=group_value, value=expected_value),
            "explanation": (
                f"{evidence_count} of {total} historical postings with "
                f"{group_field}={group_value} use {value_field}={expected_value}."
            ),
            "validation_check": check_template.format(group=group_value, value=expected_value),
            "confidence": round(confidence, 2),
            "evidence_count": evidence_count,
            "line_ids": [
                _line_id(entry) for entry in entries
                if entry.get(group_field) == group_value
                and entry.get(value_field) == expected_value
            ][:3],
            "evidence_examples": _examples(
                entries,
                lambda entry: (
                    entry.get(group_field) == group_value
                    and entry.get(value_field) == expected_value
                ),
            ),
        })

    rules.sort(key=lambda rule: (rule["confidence"], rule["evidence_count"]), reverse=True)
    return rules[:MAX_RULES_PER_KIND]


def _recurring_text_account_rules(entries: list[dict]) -> list[dict]:
    grouped: dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        booking_text = entry.get("booking_text")
        gl_account = entry.get("gl_account")

        if not booking_text or not gl_account:
            continue

        grouped[booking_text][gl_account] += 1

    rules = []
    for booking_text, counts in grouped.items():
        total = sum(counts.values())
        if total < MIN_EVIDENCE_COUNT:
            continue

        expected_account, evidence_count = counts.most_common(1)[0]
        confidence = evidence_count / total
        if confidence < MIN_CONFIDENCE:
            continue

        rules.append({
            "type": "recurring_text_account",
            "title": f"Use G/L {expected_account} for '{booking_text}'",
            "explanation": (
                f"This booking text appears {total} times; {evidence_count} postings "
                f"use G/L {expected_account}."
            ),
            "validation_check": (
                f"When booking_text is '{booking_text}', validate that gl_account is {expected_account}."
            ),
            "confidence": round(confidence, 2),
            "evidence_count": evidence_count,
            "line_ids": [
                _line_id(entry) for entry in entries
                if entry["booking_text"] == booking_text
                and entry["gl_account"] == expected_account
            ][:3],
            "evidence_examples": _examples(
                entries,
                lambda entry: (
                    entry["booking_text"] == booking_text
                    and entry["gl_account"] == expected_account
                ),
            ),
        })

    rules.sort(key=lambda rule: (rule["confidence"], rule["evidence_count"]), reverse=True)
    return rules[:MAX_RULES_PER_KIND]


def derive_rules(entries: list[dict]) -> list[dict]:
    if not entries:
        return []

    rules = [
        *_dominant_rules(
            entries,
            group_field="gl_account",
            value_field="tax_code",
            rule_type="account_tax",
            title_template="Use tax code {value} with G/L {group}",
            check_template="When gl_account is {group}, validate that tax_code is {value}.",
        ),
        *_dominant_rules(
            entries,
            group_field="gl_account",
            value_field="cost_center",
            rule_type="account_cost_center",
            title_template="Use cost center {value} with G/L {group}",
            check_template="When gl_account is {group}, validate that cost_center is {value}.",
        ),
        *_recurring_text_account_rules(entries),
    ]

    rules.sort(key=lambda rule: (rule["confidence"], rule["evidence_count"]), reverse=True)
    return rules[:MAX_TOTAL_RULES]
