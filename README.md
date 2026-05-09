# Booking Insights

Skeleton for a small web app that analyzes accounting journal entries.

## Stack

- Backend: FastAPI
- Frontend: Next.js App Router with TypeScript
- Data: added in a later feature commit

## Setup

```bash
make install
make dev-backend
make dev-frontend
```

Open http://localhost:3000.

## VS Code

The workspace includes `.vscode/settings.json` so Python analysis uses the backend virtual environment after `make install`.

If imports are still unresolved, select this interpreter manually:

```text
backend/.venv/bin/python
```

## Structure

```text
backend/
  app/
    main.py
    models.py
    services/
      anomaly_detection.py
      duplicate_detection.py
      booking_manual.py
  tests/
frontend/
  app/
  components/
  lib/
```

## Architecture Decisions

- The backend owns data loading and detection logic.
- The frontend is presentation-only and calls the backend through `/api/*`.
- Insight features are separated by service module so each heuristic can be developed and tested independently.

## Accounting Assumptions

- Journal line amounts are positive; debit or credit side is represented by `debit_credit`.
- A balanced document has equal debit and credit totals within one cent.
- G/L account ranges, tax-code conventions, and generated sample data are introduced in later commits.

## Planned Feature Commits

- Generate SAP-like journal entry data.
- Implement anomaly and typo detection.
- Implement booking manual rule suggestions.
- Implement duplicate posting detection.
- Add self-review findings and follow-up fixes.
