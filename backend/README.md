# Backend

Python services for ingestion, lakehouse layers, features, ML, orchestration, and APIs.

## Layout

- `app/` — application packages (`config`, `ingestion`, `lakehouse`, `features`, `ml`, `orchestration`, `api`, `utils`)
- `tests/` — test suite
- `infra/` — deployment / IaC assets
- `data/sample/` and `data/seeds/` — local sample data and seed files

## Quick check

```bash
python app/bootstrap_check.py
```

Install dependencies:

```bash
pip install -r requirements.txt
```
