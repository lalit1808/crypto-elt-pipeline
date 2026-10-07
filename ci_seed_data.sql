CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.all_crypto_data (
    coin_id VARCHAR(100) NOT NULL,
    price_date DATE NOT NULL,
    price_eur NUMERIC,
    market_cap_eur NUMERIC,
    volume_eur NUMERIC,
    loaded_at TIMESTAMP NOT NULL,
    PRIMARY KEY (coin_id, price_date)
);

CREATE TABLE raw.daily_crypto (
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

INSERT INTO raw.all_crypto_data (coin_id, price_date, price_eur, market_cap_eur, volume_eur, loaded_at) VALUES
('bitcoin', '2026-09-01', 68000, 1350000000000, 24000000000, NOW()),
('bitcoin', '2026-09-02', 68500, 1360000000000, 24500000000, NOW()),
('ethereum', '2026-09-01', 2350, 285000000000, 12500000000, NOW()),
('ethereum', '2026-09-02', 2380, 287000000000, 12700000000, NOW());

INSERT INTO raw.daily_crypto (coin_id, price_eur, market_cap_eur, market_cap_rank, volume_eur, price_change_pct_24h, snapshot_at, loaded_date) VALUES
('bitcoin', 70000, 1400000000000, 1, 25000000000, 1.2, '2026-10-01 10:00:00', '2026-10-01'),
('bitcoin', 70500, 1405000000000, 1, 25100000000, 1.5, '2026-10-01 23:00:00', '2026-10-01'),
('ethereum', 2400, 290000000000, 2, 13000000000, 0.8, '2026-10-01 10:00:00', '2026-10-01'),
('ethereum', 2420, 292000000000, 2, 13100000000, 1.1, '2026-10-01 23:00:00', '2026-10-01');