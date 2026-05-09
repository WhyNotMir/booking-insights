.PHONY: install seed dev-backend dev-frontend test clean

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

seed:
	cd backend && .venv/bin/python scripts/generate_data.py

dev-backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest

clean:
	rm -rf backend/.venv frontend/node_modules frontend/.next
	find backend -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
