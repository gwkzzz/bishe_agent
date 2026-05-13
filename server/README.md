# Server

FastAPI business service. It owns authentication, cases, evidence metadata, task state,
document persistence, and communication with the algorithm service.

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Alembic config is in `alembic.ini`; the initial migration creates the M1 business,
knowledge, task, and audit tables.
