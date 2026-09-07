# ACME Salary Management

Salary management for a 10,000-employee, multi-country organisation.
Built for the HR Manager persona.

See [docs/requirements.md](docs/requirements.md) for goal, scope and
deliberate exclusions.

## Status

In development. Built test-first; the commit history shows the
red / green / refactor cycles.

## Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI |
| Persistence | SQLAlchemy 2.0 + Alembic, SQLite |
| Frontend | Next.js, shadcn/ui |
| Tests | pytest, in-memory SQLite |
| Quality | ruff, mypy, GitHub Actions |
