import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services import anomaly_detection, booking_manual, duplicate_detection

DATA_PATH = Path(__file__).resolve().parent / "data" / "journal_entries.json"

app = FastAPI(title="Booking Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def load_entries() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    return json.loads(DATA_PATH.read_text())


@app.get("/health")
def health():
    return {"status": "ok", "entries_loaded": len(load_entries())}


@app.get("/entries")
def get_entries():
    return load_entries()


@app.get("/insights/anomalies")
def get_anomalies():
    return anomaly_detection.detect(load_entries())


@app.get("/insights/duplicates")
def get_duplicates():
    return duplicate_detection.detect(load_entries())


@app.get("/insights/manual")
def get_manual():
    return booking_manual.derive_rules(load_entries())
