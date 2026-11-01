# FX Tracker

A currency exchange rate tracker with a free tier and a paid tier. Free users get rates under a minute old and an honest freshness label. Paid users get rates under 2 seconds old plus 30-day history.

- **Frontend:** https://realtime-exchange-rate-tracker.vercel.app
- **Backend:** https://realtime-exchange-rate-tracker.fastapicloud.dev ([try it](https://realtime-exchange-rate-tracker.fastapicloud.dev/api/rates?base=USD&tier=free))

The reasoning behind every choice is in [decisions.md](decisions.md).

## Initial thought process

_To be written by the author._

## Run it locally

You need Python 3.13+ with [uv](https://docs.astral.sh/uv/), plus Node 24 with [pnpm](https://pnpm.io/).

**Backend** (http://localhost:8000):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000 --env-file .env
```

Redis is optional locally. Put `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in `backend/.env` to use it. Without them (drop `--env-file`) the backend uses an in-memory store.

**Frontend** (http://localhost:5173):

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend calls `http://localhost:8000` unless `VITE_API_URL` is set.

**Tests:**

```bash
cd backend && uv run pytest
cd frontend && pnpm test
```

## The endpoint

`GET /api/rates?base=EUR&tier=free|paid&verify=true`

```json
{
  "base": "EUR",
  "rates": { "USD": 1.118, "INR": 106.1 },
  "fetchedAt": "2026-11-01T10:17:30Z",
  "ageSeconds": 4,
  "source": "coinbase",
  "freshness": "fresh",
  "tier": "free",
  "verified": false
}
```

- `source` is `coinbase`, `open-er-api` or `premium`.
- `freshness` is `fresh`, `stale` or `very_stale`, worked out for the tier that asked.
- `verify=true` (free tier) asks for a premium-checked rate. It spends from a capped daily budget.
- Returns 503 only when no source has ever answered.

## Environment variables

| Where | Variable | Purpose |
|---|---|---|
| Backend | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Shared cache, refresh lock and budget counters |
| Backend | `ALLOWED_ORIGIN` | Frontend origin(s) for CORS, comma separated. Defaults to `*` |
| Backend | `FREE_FALLBACK_CAP`, `FREE_VERIFY_CAP` | Daily premium budget for free users (defaults 1500 and 3500) |
| Backend | `COINBASE_URL`, `OPEN_ER_API_URL` | Override provider URLs (useful for failure drills) |
| Frontend | `VITE_API_URL` | Backend base URL |

## Deploying

- **Backend:** [FastAPI Cloud](https://fastapicloud.com). From `backend/`, run `uv run fastapi deploy`, then set the env vars above with `uv run fastapi cloud env set`.
- **Redis:** a free [Upstash](https://upstash.com) Redis database. Copy its REST URL and token into the backend env vars.
- **Frontend:** a [Vercel](https://vercel.com) project from this repo with root directory `frontend/` and `VITE_API_URL` set to the backend URL.

## Try the failure states

```bash
# Coinbase down: falls back to daily data, labelled very_stale
COINBASE_URL=https://coinbase.invalid uv run uvicorn app.main:app --port 8000

# Every source down on a cold start: clean 503, the UI shows a retry message
COINBASE_URL=https://coinbase.invalid OPEN_ER_API_URL=https://er.invalid uv run uvicorn app.main:app --port 8000

# Verify budget of 3: send verify=true requests 16s+ apart (results are reused for 15s);
# the 4th comes back verified=false
FREE_VERIFY_CAP=3 uv run uvicorn app.main:app --port 8000
```

## Layout

```
backend/app/
  main.py            FastAPI app, wiring and the /api/rates route
  rates_service.py   tier logic, single-flight, refresh lock, fallback chain
  providers/         coinbase, open_er_api, premium (stub)
  store/             Redis and in-memory stores
  budget.py          daily premium counters
  reconcile.py       2% sanity check against the daily reference
frontend/src/
  hooks/useRates.ts  polling, offline handling, localStorage first paint
  components/        FreshnessBadge, RatesTable, Converter, HistoryCard, TierToggle
  constants/         user-facing copy and config
```
