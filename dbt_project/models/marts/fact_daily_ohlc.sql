{{ config(tags=['daily_summary']) }}

with snapshots as (
    select
        coin_id,
        loaded_date as price_date,
        price_eur,
        market_cap_eur,
        volume_eur,
        snapshot_at,
        row_number() over (partition by coin_id, loaded_date order by snapshot_at asc) as rn_open,
        row_number() over (partition by coin_id, loaded_date order by snapshot_at desc) as rn_close
    from {{ ref('stg_daily_crypto') }}
    where loaded_date < current_date
),

daily_summary as (
    select
        coin_id,
        price_date,
        avg(price_eur) as avg_price_eur,
        avg(market_cap_eur) as avg_market_cap_eur,
        avg(volume_eur) as avg_volume_eur,
        max(price_eur) as high_price_eur,
        min(price_eur) as low_price_eur,
        max(case when rn_open = 1 then price_eur end) as open_price_eur,
        max(case when rn_close = 1 then price_eur end) as close_price_eur
    from snapshots
    group by coin_id, price_date
)

select
    coin_id,
    price_date,
    open_price_eur,
    close_price_eur,
    high_price_eur,
    low_price_eur,
    avg_price_eur,
    avg_market_cap_eur,
    avg_volume_eur,
    round(
        (close_price_eur - open_price_eur) / open_price_eur * 100,
        2
    ) as movement_pct_of_the_day
from daily_summary
order by price_date desc, coin_id