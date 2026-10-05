CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.all_crypto_data (
    coin_id VARCHAR(100) NOT NULL,
    price_date DATE NOT NULL,
    price_eur NUMERIC,
    market_cap_eur NUMERIC,
    volume_eur NUMERIC,
    loaded_at TIMESTAMP NOT NULL,
    PRIMARY KEY (coin_id, price_date)
);
