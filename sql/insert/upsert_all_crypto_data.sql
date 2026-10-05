INSERT INTO raw.all_crypto_data
    (coin_id, price_date, price_eur, market_cap_eur, volume_eur, loaded_at)
VALUES %s
ON CONFLICT (coin_id, price_date) DO UPDATE SET
    price_eur = EXCLUDED.price_eur,
    market_cap_eur = EXCLUDED.market_cap_eur,
    volume_eur = EXCLUDED.volume_eur,
    loaded_at = EXCLUDED.loaded_at;
