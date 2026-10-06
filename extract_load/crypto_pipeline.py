import os
import sys
import time
import logging
from datetime import datetime, date

import requests
import psycopg2
from psycopg2.extras import execute_values

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(PIPELINE_DIR, "..", "sql")
CONFIG_DIR = os.path.join(PIPELINE_DIR, "..", "configs")
sys.path.insert(0, CONFIG_DIR)

from config import (
    DB_CONFIG,
    TRACKED_UNIVERSE_SIZE,
    HISTORICAL_DAYS,
    API_BASE,
    REQUEST_DELAY_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


def load_sql(relative_path):
    full_path = os.path.join(SQL_DIR, relative_path)
    with open(full_path, "r") as f:
        return f.read()


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(load_sql("extract/create_all_crypto_data.sql"))
    cur.execute(load_sql("extract/create_daily_crypto.sql"))

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Tables ensured: raw.all_crypto_data, raw.daily_crypto")


def get_tracked_coins(limit=TRACKED_UNIVERSE_SIZE):
    url = f"{API_BASE}/coins/markets"
    params = {
        "vs_currency": "eur",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    coins = response.json()
    coin_ids = [coin["id"] for coin in coins]
    logger.info(f"Tracked universe: {len(coin_ids)} coins")
    return coin_ids


def get_known_coin_ids():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT coin_id FROM raw.all_crypto_data;")
    known = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    return known


def backfill_single_coin(coin_id, days=HISTORICAL_DAYS):
    upsert_sql = load_sql("insert/upsert_all_crypto_data.sql")
    conn = get_connection()
    cur = conn.cursor()

    url = f"{API_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "eur", "days": str(days)}

    response = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                logger.warning(f"Rate limited on {coin_id}, waiting {wait_time}s (attempt {attempt + 1}/3)")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            break
        except requests.RequestException as e:
            logger.warning(f"Error fetching {coin_id} on attempt {attempt + 1}: {e}")
            response = None
            time.sleep(REQUEST_DELAY_SECONDS)

    if response is None or response.status_code != 200:
        logger.warning(f"Giving up backfilling {coin_id} after 3 attempts")
        cur.close()
        conn.close()
        return 0

    data = response.json()
    prices = data.get("prices", [])
    market_caps = data.get("market_caps", [])
    volumes = data.get("total_volumes", [])

    if not (len(prices) == len(market_caps) == len(volumes)):
        logger.warning(f"Skipping backfill for {coin_id}: mismatched array lengths")
        cur.close()
        conn.close()
        return 0

    loaded_at = datetime.now()
    daily_values = {}
    for i in range(len(prices)):
        ts_ms, price = prices[i]
        _, market_cap = market_caps[i]
        _, volume = volumes[i]
        price_date = datetime.fromtimestamp(ts_ms / 1000).date()
        if price_date not in daily_values:
            daily_values[price_date] = {"prices": [], "market_caps": [], "volumes": []}
        daily_values[price_date]["prices"].append(price)
        daily_values[price_date]["market_caps"].append(market_cap)
        daily_values[price_date]["volumes"].append(volume)

    rows = []
    for price_date, values in daily_values.items():
        avg_price = sum(values["prices"]) / len(values["prices"])
        avg_market_cap = sum(values["market_caps"]) / len(values["market_caps"])
        avg_volume = sum(values["volumes"]) / len(values["volumes"])
        rows.append((coin_id, price_date, avg_price, avg_market_cap, avg_volume, loaded_at))

    execute_values(cur, upsert_sql, rows)
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Backfilled {len(rows)} historical rows for new coin {coin_id}")
    return len(rows)


def backfill_new_coins(coin_ids):
    known = get_known_coin_ids()
    new_coins = [c for c in coin_ids if c not in known]

    if not new_coins:
        logger.info("No new coins detected in tracked universe")
        return 0

    logger.info(f"New coins detected, backfilling history: {new_coins}")
    total = 0
    for coin_id in new_coins:
        total += backfill_single_coin(coin_id)
        time.sleep(REQUEST_DELAY_SECONDS)
    return total


def extract_normalize_load_historical(coin_ids, days=HISTORICAL_DAYS):
    total_rows = 0
    for index, coin_id in enumerate(coin_ids):
        total_rows += backfill_single_coin(coin_id, days)
        if (index + 1) % 3 == 0:
            logger.info("Pausing 30s after 3 coins to respect rate limits")
            time.sleep(30)
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f"Historical load complete: {total_rows} rows upserted total")
    return total_rows


def extract_normalize_load_daily(coin_ids):
    upsert_sql = load_sql("insert/upsert_daily_crypto.sql")

    url = f"{API_BASE}/coins/markets"
    params = {
        "vs_currency": "eur",
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "per_page": len(coin_ids),
        "page": 1,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    coins = response.json()

    conn = get_connection()
    cur = conn.cursor()
    today = date.today()

    rows = []
    for coin in coins:
        rows.append((
            coin["id"],
            coin.get("current_price"),
            coin.get("market_cap"),
            coin.get("market_cap_rank"),
            coin.get("total_volume"),
            coin.get("price_change_percentage_24h"),
            coin.get("last_updated"),
            today,
        ))

    execute_values(cur, upsert_sql, rows)
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Daily snapshot loaded: {len(rows)} rows for {today}")
    return len(rows)


def run_daily_job():
    logger.info("Starting crypto snapshot pipeline job")
    ensure_tables()
    coin_ids = get_tracked_coins()
    backfill_new_coins(coin_ids)
    extract_normalize_load_daily(coin_ids)
    logger.info("Crypto snapshot pipeline job complete")


if __name__ == "__main__":
    run_daily_job()