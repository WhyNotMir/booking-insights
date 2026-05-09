# Booking Insights

Small web app over SAP-like journal entries that flags suspicious booking texts, possible duplicate postings, and recurring booking-rule patterns. Detection is heuristic — every finding has an auditable list of criteria and a trail back to specific lines.

## Stack

- **Backend:** FastAPI, Python 3.11+, stdlib-only detection (`difflib`, `re`, `collections`).
- **Frontend:** Next.js 15 App Router + TypeScript, plain CSS.
- **Data:** synthetic journal entries committed as JSON; regenerable via `make seed`.
- **Tests:** pytest, integration-style over the committed data.

## Setup

```bash
make install        # backend venv + frontend npm install
make seed           # regenerate journal_entries.json
make dev-backend    # FastAPI on :8000   (terminal 1)
make dev-frontend   # Next.js on :3000   (terminal 2; falls back to :3001)
make test
```

Open <http://localhost:3000>. The frontend proxies `/api/*` to the backend via `next.config.js` — no CORS in dev, same path in any production deployment. `.vscode/settings.json` points the Python interpreter at `backend/.venv/bin/python` after `make install`.

## Repository structure

```text
backend/
  app/
    main.py                    FastAPI routes
    models.py                  JournalLine pydantic model
    data/journal_entries.json  committed seed
    services/
      _helpers.py              shared line_id / line_sample
      anomaly_detection.py
      duplicate_detection.py
      booking_manual.py
  scripts/generate_data.py
  tests/test_services.py
frontend/
  app/                         layout, page, globals.css
  components/                  BookingTable + 3 finding sections
  lib/                         api.ts, types.ts
Makefile
```

## Architecture decisions

- **Two services, one frontend.** Detection in Python (stdlib heuristics fit naturally), UI is presentation-only and fetches via `/api/*`.
- **Sample data is committed.** Customer doesn't have to seed to see the app working. `make seed` is deterministic (`random.seed(42)`).
- **stdlib-only detection.** No `rapidfuzz`/`pandas`. Dataset is ~450 lines and heuristics are simple — extra wheels would be unjustified.
- **One module per detector.** Shared field helpers in `_helpers.py`, no shared business logic — each detector can be tuned and tested in isolation.

## Scope choices

- **No pandas or fuzzy-matching dependency.** The dataset is small enough for stdlib collections and `difflib`; avoiding extra dependencies keeps setup simple.
- **Committed JSON seed plus generator.** The app can run immediately, while `make seed` still shows how the journal data is produced.
- **Heuristics instead of ML.** Accounting review needs explainable criteria and evidence lines more than opaque model output.


## Accounting assumptions

- The dataset is fully synthetic and models the booking system of a fictional hotel group operating across multiple European countries (`AT01`, `DE01`, `ES01`, `IT01`, `NL01`).
- One JSON object = one journal line; `document_id` groups lines into a posting.
- Positive `amount` = debit, negative = credit; `debit_credit` carries the same information as a redundant indicator (SAP Universal Journal style).
- Journal-entry lines contain ERP-style accounting fields such as company code, posting date, G/L account, cost center, booking text, tax code, and vendor/customer references.
- Each document satisfies `sum(amount) == 0` (within €0.01).
- VAT simplified to `V20` / `V10` / `EXEMPT`; G/L numbers are SAP-shaped samples, not a real chart.
- Single currency (EUR).


## Data generation

`scripts/generate_data.py` produces ~455 lines, 143 documents, 24 G/L accounts over Jan–Feb 2026. Three classes of suspicious cases are intentionally planted as ground truth for the detectors:

- **Typos** in a few booking texts (`Sofware Subscription`, `Maintenence Invoice`, `Office Supply Invoice`).
- **Possible duplicates** — three full documents cloned with a 1–3 day shift into `DOC9991/9992/9993`.
- **Unusual account/text combo** — a `Room Revenue` line booked to G/L 580000 (legal expense) instead of revenue.

## Detection features

### 1. Anomaly detection — `app/services/anomaly_detection.py`

- **Text variants:** flags rare booking texts (≤ 1 occurrence) that resemble a recurring text (≥ 0.76 `SequenceMatcher` ratio) within the same role suffix (`vat`/`payable`/`receivable`).
- **Unusual account/text combos:** for each booking text where one G/L account dominates ≥ 70%, flag any other account paired with that text.

Trade-off: flags every offending line separately rather than collapsing them. Fine at this scale.

### 2. Duplicate detection — `app/services/duplicate_detection.py`

Block by `(amount, currency, debit_credit)`, score each cross-document pair on five criteria summing to 1.00:

| Criterion | Max contribution |
| --- | --- |
| Amount match (implicit from blocking) | +0.15 |
| Same vendor or customer | +0.25 |
| `booking_text` similarity | +0.30 |
| Posting-date proximity (≤ 7 days) | +0.20 |
| Same `gl_account` | +0.10 |

Line-pairs above 0.70 confidence are aggregated into **document-level clusters** — one finding per duplicate posting, not N findings for an N-line invoice booked twice.

Trade-off: exact-amount blocking misses near-amount duplicates (off-by-cent rounding). A second pass with tolerance is the natural next step.

### 3. Booking manual — `app/services/booking_manual.py`

Three rule kinds derived by frequency analysis (`MIN_EVIDENCE_COUNT` = 5, `MIN_CONFIDENCE` = 0.75 dominance):

- `account_tax` — dominant tax code per G/L account.
- `account_cost_center` — dominant cost-centre per G/L account.
- `recurring_text_account` — dominant G/L account per booking text.

Each rule emits a `validation_check` ("When `gl_account` is X, validate `tax_code` is Y") and three `evidence_examples` from supporting postings.

## Tests

`backend/tests/test_services.py` — integration tests over the committed JSON. Verifies: empty input gives empty output, planted typos surface, the unusual `Room Revenue` / 580000 combo surfaces, all three rule kinds are derived, and duplicate detection produces clusters spanning `DOC9991/9992/9993` with descending confidence. Run with `make test`.

## Self-review

Five concrete findings from a post-implementation audit. **#1, #4, and #5 are implemented in follow-up commits.**

1. **Architecture — duplicated `_line_sample` / `_line_id` across detectors.** Three services had near-identical helpers but with different field shapes (8 vs 12). Extracted `app/services/_helpers.py` so every finding embeds the same payload. Implemented.

2. **Correctness — late-binding lambdas in `booking_manual` (`_dominant_rules`).** Predicates close over loop variables and only work today because `_examples` consumes them eagerly. *Fix:* default-argument capture (`lambda entry, gv=group_value: …`).

3. **DX — endpoints return opaque `list[dict]`.** No OpenAPI schema, frontend `Insight`/`DuplicateCandidate` types are TS-only. *Fix:* TypedDict/Pydantic response models with `response_model=` on routes; generate frontend types from OpenAPI.

4. **Operations — `lru_cache` on `load_entries` never invalidates.** After `make seed` while the dev server runs, the cached list is served until restart — caused a stale 500 during development. Fixed by keying the cache on `os.path.getmtime(DATA_PATH)`. Implemented.

5. **UX — sections didn't show finding counts.** No scope before scrolling. *Fix:* added compact count summaries inside each data section for journal lines, anomaly findings, duplicate candidates, and booking-manual checks. Implemented.

## Task 3 — Knowledge graph context

A sketch of how a contextual layer could explain the *why* behind a posting — *why was this discount granted?*, *why is this KPI calculated this way?* — by linking each accounting fact to the surrounding business context.

- **Beyond Accounting Facts:** Extend anomaly detection by comparing journal entries against historical baselines and investigating unusual deviations using external business context such as discounts, promo codes, refunds, cancellations, and manual overrides.
- **Core Context Sources:** Integrate the Booking/Reservation System (original price, final price, voucher, promo code, booking channel) and CRM systems (negotiated rates, customer notes, manual adjustments, corporate agreements).
- **Unstructured Context Sources:** Use emails, approval logs, SOPs, and policy documents to capture the "soft" business logic behind pricing exceptions, approvals, and accounting decisions.
- **Knowledge Graph Relationships:** Connect entities through a lightweight graph structure such as `JournalEntry → Booking → Customer → CRM Note → Approval → Policy` and `KPI → Definition → Query/Transformation → Owner → Approval`.
- **Hybrid Retrieval Strategy:** Combine deterministic matching (`document_id`, `booking_id`, `customer_id`) with vector search for unstructured text (emails, CRM notes, policies) and graph traversal for structured relationships.
- **Evidence-First Explanation Flow:** The system first retrieves supporting evidence (booking records, CRM notes, approvals, policy excerpts) and only then allows the LLM to generate an explanation, preventing unsupported reasoning.
- **Explainable Investigation Pipeline:** Instead of returning only "anomaly detected", the system should explain whether a transaction is a valid business exception, an approved adjustment, or a potentially incorrect posting.
- **Risk 1:** incorrect entity linking between accounting records and external systems (CRM, booking engine, email records). **Mitigation:** prioritize deterministic IDs and attach confidence scores to fallback matches. 
- **Risk 2:** hallucinated explanations generated by the LLM without supporting evidence. **Mitigation:** enforce evidence-first retrieval, require citations to retrieved records/documents, and return “insufficient context” when no reliable explanation exists.
