INSERT INTO raw.daily_crypto
    (coin_id, price_eur, market_cap_eur, market_cap_rank,
     volume_eur, price_change_pct_24h, snapshot_at, loaded_date)
VALUES %s
ON CONFLICT (coin_id, snapshot_at) DO NOTHING;