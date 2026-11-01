# Decisions

The problem isn't really "rates aren't real-time". Free users see errors and numbers that are 30 to 60 minutes behind Google. They stop trusting the product before they ever think about paying. Everything below is built around one rule: **every number on screen is either fresh or honestly labelled with its age. The page never turns into an error screen.**

## Which APIs and why

| Role | API | Why |
|---|---|---|
| Free primary | Coinbase `/v2/exchange-rates` | No key, near real-time fiat rates, one call returns every currency |
| Free fallback | open.er-api.com (ExchangeRate-API open tier) | No key, 166 currencies, very reliable. Only updates daily but tells you when |
| Daily reference | open.er-api.com | Used as the sanity check for Coinbase (see conflicts) |
| Premium | `PremiumProvider` stub | The brief says to assume it exists. See below |
| History | Frankfurter (ECB) | Free 30-day series. Powers the paid-only chart |

One call with base USD covers every pair. Cross rates are `usd[B] / usd[A]`. That one fact drives the whole budget: a single upstream call refreshes the data for every free user at once.

**The premium stub** calls Coinbase with a longer timeout and labels the result `premium`. It returns real data and never made-up numbers. Everything around it is real: tier routing, the budget meter and the cache writes. Swapping in a real vendor means replacing one class (`backend/app/providers/premium.py`).

## Architecture in one paragraph

There's one shared cache (`rates:USD` in Upstash Redis) and each tier has its own maximum age. **Paid** (≤ 2s): if the cache is older, the request waits for a premium fetch. Concurrent paid requests on the same instance share that one call. **Free** (≤ 60s): if the cache is older, the first request to grab a Redis lock refreshes it inline (about 200ms) and everyone else gets the cached data instantly. There's no cron and no background work. The backend runs on FastAPI Cloud, which scales to zero. Timers don't survive that. Freshness is driven by traffic: no visitors means no upstream calls.

## Fallback strategy

Free path, in order:
1. Serve the cache if it's under 60s old.
2. Coinbase (2s timeout).
3. open.er-api (2s timeout). Stamped with its **publish** time so daily data is never shown as fresh.
4. If both fail or the best data we have is more than 5 minutes old: **one premium call** from the free budget's fallback reserve. That one call fixes the data for every free user, which is why it's cheap.
5. If even that fails, serve the last cached snapshot with its real age.
6. Only when there has never been any data at all: `503 { error, retryAfterSeconds }`. The UI turns that into a friendly message with a retry button.

Paid path: premium, then the last snapshot labelled stale. Paid users never wait on the free sources.

If Redis is down, the cache falls back to memory per instance and the budget **fails closed**: no free-tier premium spend while we can't count it.

## The $5/day (5,000 premium calls) for free users

Two daily counters in Redis, keyed by UTC date, counted on **attempt** (not success) so a flaky vendor can't push spend over the cap:

| Bucket | Cap | Spent when |
|---|---|---|
| `premium:free-fallback` | 1,500 | Free sources failed or the data is more than 5 min old. At most one call per refresh window: a whole day of Coinbase downtime costs about 1,440 calls |
| `premium:free-verify` | 3,500 | A free user types an amount in the converter. That's the high-intent moment just before they act on the number. It's also when a wrong rate becomes a support ticket. Debounced 600ms and reused for 15s across all users |

When a cap is hit, users still get free-source rates, just without the "verified" tick. Paid usage is counted (`premium:paid`) but not capped, because it's covered by the $9 plan.

**Paid cost check:** the worst case is a premium call every 2s all day, about 43K calls or roughly $43/day. 200 paid users × $9 works out to about $60/day. That fits but the margin is thin. The 2s window is a cost lever as well as a product one: moving to 5s halves the cost.

## Conflicting data

Coinbase is checked against the daily open.er-api reference (cached for 6h). If a currency differs by **more than 2%**, the reference value wins for that currency and the gap is logged. Major currencies rarely move 2% in a day. A gap that size more likely means a bad feed than a real market move. The cost is that a real 2%+ move shows the daily rate until the reference catches up. I accept that for a free tier, since a briefly conservative number does less damage than a wrong one.

## What users see when things fail or go stale

The server decides freshness for each tier (free: fresh ≤ 60s, stale ≤ 10 min; paid: fresh ≤ 5s, stale ≤ 60s). The UI shows it in a badge that's always visible:

- **Fresh:** green, "Updated 12s ago via Coinbase", ticking every second.
- **Stale / very stale:** amber or red, plus "Rates may be outdated. Showing the last known rates."
- **Backend unreachable:** last known rates stay on screen, plus "Can't reach the rates service right now." Changing the base currency still works because the client rebases the cached rates.
- **Cold start** (FastAPI Cloud waking up): the last response is saved in localStorage and shown instantly with its real age while the backend wakes.
- **Never had data:** "Rates are temporarily unavailable" plus a retry button. Never a blank page or a raw error.

Data we couldn't refresh is never shown green, whatever the server said at the time.

## What I did about staleness

- Coinbase replaces the daily-only APIs as the primary source. Free data is now seconds to a minute old, down from 30 to 60 minutes.
- Requests drive the refreshes. The cache is at most 60s old whenever anyone is looking.
- Paid traffic refreshes the shared cache every ~2s. Free users often get data a few seconds old at no extra cost.
- Daily fallback data is stamped with when it was published, not when we fetched it. It can't pretend to be fresh.

## How free and paid differ

Freshness isn't the paywall. "Under 60s" and "under 2s" look almost the same to a traveller. The PM's point is that free users need *trust*, not real-time data. Paid gets guaranteed live rates, uptime that doesn't depend on free sources and **30-day history**. History is the one paid feature I built. Free users see it blurred behind an upgrade prompt, which gives an upgrade path you can see in the demo without building billing.

`tier` is a query param plus a demo toggle, standing in for auth. In production the tier would come from the session, never from the client.

## What I cut

- Auth and billing (the toggle stands in for both).
- Rate alerts and CSV export (see below).
- Server-Sent Events. Polling (paid 3s, free 30s) is enough at this scale.
- Single-flight across instances for paid. Rare duplicate premium calls across instances are accepted.
- Observability dashboards. Logs only.
- Currencies outside a fixed set of 32 fiat codes. History only covers the ~30 currencies the ECB publishes.

## What I'd add with more time

1. **Rate alerts** ("tell me when EUR→INR hits 92"). This is the strongest reason for freelancers to pay.
2. A dashboard with: share of free responses that are `very_stale`, 95th-percentile age of data shown to free users, premium spend per bucket and verify-to-upgrade conversion. These are the leading indicators for "trust". Tickets and conversion lag behind them.
3. Real auth, with the tier read from the session.
4. A second free fiat source. Then we could take a median of three instead of one primary checked against one reference.
5. Rate limiting per client on `verify=1`. Today a single free user could burn through the verify budget.

## Other thoughts

- **Licensing:** real premium vendors often forbid serving their data to non-paying users. If that applied, the fix is separate cache keys (`rates:premium:USD` and `rates:free:USD`), with only paid requests reading the premium one. Today's shared cache assumes we're allowed to.
- open.er-api's terms require attribution, which is in the footer.
- Built with Claude Code as a pairing partner: the architecture was worked out in conversation and the code was generated, then reviewed and tested.
