"""Detect potential duplicate journal postings.

Strategy:
  1. Block by (rounded amount, currency, debit_credit). Pairs only form
     within a block, which cuts the comparison from N^2 to roughly N * k
     where k is the average block size.
  2. Score each cross-document line-pair on five criteria:
       amount match  (implicit from blocking)         +0.15
       same vendor or customer                         +0.25
       booking_text similarity (stdlib SequenceMatcher) up to +0.30
       posting_date proximity (<= 7 days)              up to +0.20
       same gl_account                                 +0.10
     Maximum line-pair confidence = 1.00.
  3. Cluster line-pairs by (document_a, document_b). Document-level
     confidence = mean of line-pair confidences in the cluster. This is
     what surfaces in the UI: one finding per duplicate document, with
     all underlying lines visible as evidence.

Why this design:
  - Heuristic-only, no ML — every match has an auditable list of criteria.
  - Blocking on exact amount catches the realistic duplicate case
    (someone reposts the same invoice). Near-amount duplicates would
    require a second pass and are out of MVP scope.
  - Multi-criterion scoring lets weak signals combine: same vendor +
    same amount + similar text is still suspicious if dates differ.
  - Aggregating to documents keeps the UI quiet — a 5-line invoice
    booked twice is one finding, not five.
"""

from collections import defaultdict
from datetime import date, datetime
from difflib import SequenceMatcher
import re

from app.services._helpers import line_id, line_sample

MIN_LINE_CONFIDENCE = 0.7
MAX_DATE_GAP_DAYS = 7
TEXT_SIMILARITY_FLOOR = 0.6

W_AMOUNT = 0.15
W_COUNTERPARTY = 0.25
W_TEXT = 0.30
W_DATE = 0.20
W_GL = 0.10


def _normalize_text(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize_text(a), _normalize_text(b)).ratio()


def _parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _counterparty(entry: dict) -> str | None:
    return entry.get("vendor_id") or entry.get("customer_id") or None


def _score_pair(a: dict, b: dict) -> tuple[float, list[str]]:
    score = 0.0
    criteria: list[str] = []

    # Amount + currency + side are the block key; surface them anyway so
    # the user can see what put these lines in the same bucket.
    score += W_AMOUNT
    criteria.append(f"amount {abs(a['amount']):.2f} {a['currency']}")

    cp_a = _counterparty(a)
    cp_b = _counterparty(b)
    if cp_a and cp_a == cp_b:
        score += W_COUNTERPARTY
        criteria.append(f"same counterparty {cp_a}")

    similarity = _text_similarity(a["booking_text"], b["booking_text"])
    if similarity >= TEXT_SIMILARITY_FLOOR:
        normalized = (similarity - TEXT_SIMILARITY_FLOOR) / (1 - TEXT_SIMILARITY_FLOOR)
        score += W_TEXT * normalized
        criteria.append(f"text similarity {int(similarity * 100)}%")

    gap_days = abs((_parse_date(a["posting_date"]) - _parse_date(b["posting_date"])).days)
    if gap_days <= MAX_DATE_GAP_DAYS:
        normalized = 1 - (gap_days / MAX_DATE_GAP_DAYS)
        score += W_DATE * normalized
        criteria.append(f"date gap {gap_days}d")

    if a["gl_account"] == b["gl_account"]:
        score += W_GL
        criteria.append(f"same gl_account {a['gl_account']}")

    return score, criteria


def _blocks(entries: list[dict]) -> dict[tuple, list[dict]]:
    blocks: dict[tuple, list[dict]] = defaultdict(list)
    for entry in entries:
        key = (
            round(float(entry["amount"]), 2),
            entry["currency"],
            entry["debit_credit"],
        )
        blocks[key].append(entry)
    return blocks


def _line_pair_candidates(entries: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    candidates: list[dict] = []

    for group in _blocks(entries).values():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a["document_id"] == b["document_id"]:
                    continue

                pair_key = tuple(sorted([line_id(a), line_id(b)]))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                score, criteria = _score_pair(a, b)
                if score >= MIN_LINE_CONFIDENCE:
                    candidates.append({
                        "lines": [a, b],
                        "confidence": score,
                        "criteria": criteria,
                    })

    return candidates


def _cluster_criteria(line_pairs: list[dict], doc_a: str, doc_b: str,
                      doc_a_lines: list[dict], doc_b_lines: list[dict]) -> list[str]:
    """Aggregate line-level criteria into a few document-level statements."""
    matched = len(line_pairs)
    base = min(len(doc_a_lines), len(doc_b_lines))
    summary = [f"{matched} of {base} lines match"]

    counterparties = sorted({
        cp for pair in line_pairs
        for cp in (_counterparty(pair["lines"][0]),) if cp
    })
    if counterparties:
        summary.append(f"shared counterparty {', '.join(counterparties)}")

    gap = abs(
        (_parse_date(doc_a_lines[0]["posting_date"])
         - _parse_date(doc_b_lines[0]["posting_date"])).days
    )
    summary.append(f"date gap {gap}d")

    text_similarities = [
        int(_text_similarity(p["lines"][0]["booking_text"], p["lines"][1]["booking_text"]) * 100)
        for p in line_pairs
    ]
    if text_similarities:
        summary.append(f"text similarity {min(text_similarities)}–{max(text_similarities)}%")

    return summary


def detect(entries: list[dict]) -> list[dict]:
    if not entries:
        return []

    pairs = _line_pair_candidates(entries)
    if not pairs:
        return []

    clusters: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for pair in pairs:
        doc_a, doc_b = pair["lines"][0]["document_id"], pair["lines"][1]["document_id"]
        clusters[tuple(sorted([doc_a, doc_b]))].append(pair)

    by_document: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        by_document[entry["document_id"]].append(entry)

    findings: list[dict] = []
    for (doc_a, doc_b), line_pairs in clusters.items():
        confidence = sum(p["confidence"] for p in line_pairs) / len(line_pairs)
        lines_a = by_document[doc_a]
        lines_b = by_document[doc_b]

        findings.append({
            "type": "duplicate_document",
            "title": f"Possible duplicate posting between {doc_a} and {doc_b}",
            "confidence": round(confidence, 2),
            "evidence_count": len(line_pairs),
            "criteria": _cluster_criteria(line_pairs, doc_a, doc_b, lines_a, lines_b),
            "lines": [line_sample(entry) for entry in lines_a + lines_b],
        })

    findings.sort(key=lambda f: f["confidence"], reverse=True)
    return findings
