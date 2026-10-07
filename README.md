# End-to-End Data Engineering Project

Built this to get real, hands-on DE experience - not just read about it.
Covers the whole thing: ingestion, orchestration, transformation, testing,
monitoring, alerting, CI. Used live crypto prices as the data, but this
isn't really a "crypto project" - it's a DE project that happens to use
crypto as the dataset.

## Flow

```
CoinGecko API
  -> Python (rate-limit handling, writes to Postgres)
  -> raw.daily_crypto (hourly snapshots, never deleted)
  -> raw.all_crypto_data (180-day backfill + auto-backfill for new coins)
  -> dbt staging (clean columns)
  -> dbt fact tables
       fact_daily_ohlc - open/close/high/low per finished day
       fact_price_history - full history, no gaps, incremental
  -> dbt marts
       mart_daily_top_movers
       mart_hourly_top_movers
       dim_tracked_coins - today's actual top 25, by rank

Airflow: extract -> dbt run -> dbt test -> dbt source freshness, every hour.
Slack alert on any task failure.
GitHub Actions: real Postgres service, seeded sample data, dbt run + dbt
test on every push - not just a syntax check.
```

## Dashboard

Streamlit. Price chart + 7-day forecast (straight line trend, nothing
fancy, didn't want to fake sophistication). Daily movers with a date
picker. Hourly movers, live. Dropdown only shows current top-25 coins.

## Stack

Python, Postgres, dbt, Airflow, Docker, Streamlit, GitHub Actions, Slack.

## Design decisions

- **Idempotent writes.** Every insert uses `ON CONFLICT DO UPDATE` or
  `DO NOTHING` on a proper unique key (`coin_id, snapshot_at`, etc.). The
  pipeline can be re-run or retried without creating duplicates - this is
  what makes Airflow's automatic retries safe.
- **Rate limits.** CoinGecko's free tier is strict. Backfill retries with
  exponential backoff and pauses every few coins, or it dies halfway
  through a run.
- **Hourly snapshots, never overwritten.** Lets dbt compute real
  open/high/low/close from the actual intraday spread, not just one
  averaged number.
- **Continuous coin tracking.** Originally only fetched today's top 25,
  so a coin that dropped out just stopped getting data - permanent gap
  in its history. Fixed by tracking every coin ever seen, forever, using
  the raw `market_cap_rank` field (not just presence) to still filter
  `dim_tracked_coins` down to today's actual top 25 for display. The
  naive fix (just check "is this coin in the latest snapshot") would
  have broken once every coin started getting fetched every hour.
- **dbt never writes to raw.** All transformation is read-only against
  raw tables, so logic can be reworked freely with zero risk to ingested
  data.
- **Incremental model.** `fact_price_history` uses
  `materialized='incremental'` with `unique_key=['coin_id','price_date']`
  and `is_incremental()` to only reprocess the last 2 days each run,
  instead of rebuilding the full table every hour.
- **Secrets in `.env`.** Slack webhook, DB creds, Airflow login - all
  environment variables, git-ignored, never hardcoded.

## Running it

```bash
docker compose up -d
```

Airflow: localhost:8080. Postgres: 5432.

Unpause `crypto_hourly_dag`, it runs itself from there. `crypto_historical_dag`
is manual only - no reason to hit that expensive API call daily.

Needs a `.env` at the project root (not committed) - see `.env.example`
for the required variables.

dbt directly:
```bash
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
dbt source freshness --profiles-dir .
```

Dashboard:
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Alerting and monitoring

Source freshness checks catch it if raw data stops updating (warn at 2
hours stale, error at 4). Any task failure in the hourly DAG posts
straight to Slack.

## Testing

21 `not_null`/`unique` tests across sources, staging, facts, marts. Run
locally, every hour in Airflow, and in CI against a real temporary
Postgres service on every push - actual tests against actual data, not
just a compile check.

## CI

GitHub Actions spins up Postgres, loads seed data, runs `dbt run` +
`dbt test` on every push.

## TODO

- Better forecast at some point
- CD - needs the infra hosted somewhere reachable instead of my laptop,
  which is a scope call for a portfolio project, not something I missed

## Why

Wanted real, hands-on experience with dbt alongside the SQL/Python pipelines 
I already build at work — not just reading about it. 
Built this to properly learn it: proper staging/mart structure, tests that run for real in CI,
dbt orchestrated through Airflow with monitoring and alerting, 
and a dashboard so the output's actually usable, not just sitting in a database.