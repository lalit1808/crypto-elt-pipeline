CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.daily_crypto (
    coin_id VARCHAR(100) NOT NULL,
    price_eur NUMERIC,
    market_cap_eur NUMERIC,
    market_cap_rank INTEGER,
    volume_eur NUMERIC,
    price_change_pct_24h NUMERIC,
    snapshot_at TIMESTAMP NOT NULL,
    loaded_date DATE NOT NULL,
    PRIMARY KEY (coin_id, snapshot_at)
);