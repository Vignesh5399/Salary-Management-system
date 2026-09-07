# ACME Salary Management

Salary management for a 10,000-employee, multi-country organisation.
Built for the HR Manager persona.

See [docs/requirements.md](docs/requirements.md) for goal, scope and
deliberate exclusions.

Built test-first; the commit history shows the red / green / refactor
cycles.

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


## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local     # point NEXT_PUBLIC_API_URL at the API
npm run dev                          # http://localhost:3000
```

## Full local run

```bash
# 1. a MongoDB — a free Atlas cluster is enough
export MONGODB_URL='mongodb+srv://...'

# 2. seed 10,000 employees (deterministic; same data every run)
cd backend && pip install -e ".[dev]" && python -m app.seed

# 3. API
uvicorn app.main:app --reload        # http://localhost:8000/docs

# 4. UI, in another terminal
cd ../frontend && npm install && npm run dev
```

## Deploying

No containers involved.

**API — Render web service, native Python runtime**

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -e .` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Environment | `MONGODB_URL`, `ALLOWED_ORIGINS` (your Vercel URL) |

Free instances sleep after 15 minutes idle and take about a minute to
wake, so the first request to a cold demo is slow.

**UI — Vercel**, root directory `frontend`, with `NEXT_PUBLIC_API_URL`
set to the Render URL.

**Database — MongoDB Atlas free tier.** Run the seed once against it
after deploying. Add `0.0.0.0/0` to Network Access so Render and Vercel
can reach it, or Render's static outbound IPs if you prefer.
