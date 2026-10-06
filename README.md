# Crypto ELT Pipeline

Pulls crypto prices from an API, runs them through Airflow + dbt, builds
daily summaries and gainers/losers tables. Built it to get real dbt
experience, not just theory. Has a dashboard with a basic forecast too.

## Flow

```
CoinGecko API
  -> Python (rate-limit handling, writes to Postgres)
  -> raw.daily_crypto (hourly snapshots, never deleted)
  -> raw.all_crypto_data (180-day backfill + auto-backfill for new coins)
  -> dbt staging (clean columns)
  -> dbt fact tables
       fact_daily_price_summary - open/close/high/low per finished day
       fact_crypto_price_daily - full history, no gaps
  -> dbt marts
       mart_daily_top_movers
       mart_hourly_top_movers
       dim_tracked_coins - today's actual top 25

Airflow: extract -> dbt run -> dbt test, every hour.
GitHub Actions: dbt parse on every push.
```

## Dashboard

Streamlit. Price chart + 7-day forecast (straight line trend, not a real
model, didn't want to fake it). Daily movers with a date picker. Hourly
movers, live. Dropdown only shows current top-25 coins.

## Stack

Python, Postgres, dbt, Airflow, Docker, Streamlit, GitHub Actions.

## Stuff I ran into

- CoinGecko free tier rate-limits hard. Backfill retries + pauses or it
  just fails halfway.
- Keep every hourly snapshot instead of overwriting - that's what lets
  dbt compute real open/high/low/close.
- Top-25 list changes hourly. New coins get auto-backfilled so there's
  no gap in their history.
- Had a bug where the old backfill and the new daily summary disagreed
  on the same day's numbers. Date-overlap issue in how I merged them.
- dbt never writes to raw. Read-only. Means I can change transformation
  logic without touching ingested data.

## Run it

```bash
docker compose up -d
```

Airflow: localhost:8080 (admin/admin). Postgres: 5432.

Unpause `crypto_hourly_dag`, it runs itself. `crypto_historical_dag` is
manual only - no reason to hit that expensive endpoint daily.

```bash
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
```

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

## CI

GitHub Actions runs `dbt parse` on every push.

## TODO

- Tests on the movers marts
- Incremental models instead of full rebuilds
- Better forecast eventually

## Why

Job search kept flagging dbt as a gap. Built this to actually fix that -
proper staging/mart structure, tests, dbt running through Airflow, and a
dashboard so it's not just data sitting in a database.