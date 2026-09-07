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
| Persistence | MongoDB via Beanie (see the deviation note in the requirements) |
| Frontend | Next.js, shadcn/ui |
| Tests | pytest — a fast suite with no database, plus marked integration tests |
| Quality | ruff, mypy, GitHub Actions |

## Running it

```bash
cd backend
pip install -e ".[dev]"

pytest                      # fast suite: no database, no network
mypy app && ruff check .
```

The integration tests need a MongoDB. A free Atlas cluster is enough — no
local install:

```bash
MONGODB_URL='mongodb+srv://...' pytest -m integration
```

They use a separate `salary_test` database and drop it afterwards, so the
same cluster can serve the app.
