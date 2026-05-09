"""Detect suspicious booking text and account patterns."""

from collections import Counter, defaultdict
from difflib import SequenceMatcher
import re

from app.services._helpers import line_id, line_sample

MIN_COMMON_TEXT_COUNT = 2
MAX_VARIANT_COUNT = 1
TEXT_SIMILARITY_THRESHOLD = 0.76
ACCOUNT_DOMINANCE_THRESHOLD = 0.7
ROLE_SUFFIXES = {"vat", "payable", "receivable"}


def _normalize_text(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _similarity(a: str, b: str) -> float:
    a_norm = _normalize_text(a)
    b_norm = _normalize_text(b)
    ratio = SequenceMatcher(None, a_norm, b_norm).ratio()

    a_tokens = sorted(a_norm.split())
    b_tokens = sorted(b_norm.split())
    token_ratio = SequenceMatcher(None, " ".join(a_tokens), " ".join(b_tokens)).ratio()

    return max(ratio, token_ratio)


def _role_suffix(text: str) -> str | None:
    tokens = _normalize_text(text).split()
    if not tokens:
        return None
    suffix = tokens[-1]
    return suffix if suffix in ROLE_SUFFIXES else None


def _detect_text_variants(entries: list[dict]) -> list[dict]:
    text_counts = Counter(entry["booking_text"] for entry in entries)
    common_texts = [
        text for text, count in text_counts.items()
        if count >= MIN_COMMON_TEXT_COUNT
    ]

    findings = []
    seen = set()
    for text, count in text_counts.items():
        if count > MAX_VARIANT_COUNT:
            continue

        best_match = None
        best_score = 0.0
        for candidate in common_texts:
            if candidate == text:
                continue
            if _role_suffix(text) != _role_suffix(candidate):
                continue
            score = _similarity(text, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match is None or best_score < TEXT_SIMILARITY_THRESHOLD:
            continue

        key = ("text_variant", text, best_match)
        if key in seen:
            continue
        seen.add(key)

        affected = [entry for entry in entries if entry["booking_text"] == text]
        evidence = [
            entry for entry in entries
            if entry["booking_text"] == best_match
        ][:3]
        findings.append({
            "type": "text_variant",
            "title": "Suspicious booking text variant",
            "line_ids": [line_id(entry) for entry in affected],
            "affected_lines": [line_sample(entry) for entry in affected],
            "evidence_examples": [line_sample(entry) for entry in evidence],
            "reason": f"'{text}' is rare and closely resembles recurring text '{best_match}'.",
            "explanation": "Rare near-duplicate wording can indicate a typo or inconsistent manual posting text.",
            "confidence": round(min(0.98, 0.55 + best_score * 0.4), 2),
            "evidence_count": text_counts[best_match],
        })

    return findings


def _detect_unusual_account_text_combinations(entries: list[dict]) -> list[dict]:
    text_account_counts: dict[str, Counter] = defaultdict(Counter)
    for entry in entries:
        text_account_counts[entry["booking_text"]][entry["gl_account"]] += 1

    findings = []
    for text, account_counts in text_account_counts.items():
        total = sum(account_counts.values())
        if total < MIN_COMMON_TEXT_COUNT:
            continue

        dominant_account, dominant_count = account_counts.most_common(1)[0]
        if dominant_count / total < ACCOUNT_DOMINANCE_THRESHOLD:
            continue

        for entry in entries:
            if entry["booking_text"] != text or entry["gl_account"] == dominant_account:
                continue

            evidence = [
                candidate for candidate in entries
                if candidate["booking_text"] == text
                and candidate["gl_account"] == dominant_account
            ][:3]
            findings.append({
                "type": "account_text_combo",
                "title": "Unusual account and text combination",
                "line_ids": [line_id(entry)],
                "affected_lines": [line_sample(entry)],
                "evidence_examples": [line_sample(candidate) for candidate in evidence],
                "expected_gl_account": dominant_account,
                "actual_gl_account": entry["gl_account"],
                "reason": (
                    f"'{text}' usually posts to G/L {dominant_account}, "
                    f"but this line uses G/L {entry['gl_account']}."
                ),
                "explanation": "A common posting text paired with a rare account can indicate an incorrect account assignment.",
                "confidence": round(min(0.97, 0.6 + (dominant_count / total) * 0.35), 2),
                "evidence_count": dominant_count,
            })

    return findings


def detect(entries: list[dict]) -> list[dict]:
    if not entries:
        return []

    findings = [
        *_detect_text_variants(entries),
        *_detect_unusual_account_text_combinations(entries),
    ]
    findings.sort(key=lambda finding: finding["confidence"], reverse=True)
    return findings
