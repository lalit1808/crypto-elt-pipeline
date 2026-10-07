{{
    config(
        materialized='incremental',
        unique_key=['coin_id', 'price_date']
    )
}}

with legacy_seed as (
    select
        coin_id,
        price_date,
        price_eur as avg_price_eur,
        market_cap_eur,
        volume_eur
    from {{ ref('stg_crypto_prices') }}
    where price_date not in (
        select price_date from {{ ref('fact_daily_ohlc') }}
    )

    {% if is_incremental() %}
    and price_date >= (select max(price_date) - interval '2 days' from {{ this }})
    {% endif %}
),

historical as (
    select
        coin_id,
        price_date,
        avg_price_eur,
        avg_market_cap_eur as market_cap_eur,
        avg_volume_eur as volume_eur
    from {{ ref('fact_daily_ohlc') }}
    where price_date < current_date

    {% if is_incremental() %}
    and price_date >= (select max(price_date) - interval '2 days' from {{ this }})
    {% endif %}
),

derived_today as (
    select
        coin_id,
        loaded_date as price_date,
        avg(price_eur) as avg_price_eur,
        avg(market_cap_eur) as market_cap_eur,
        avg(volume_eur) as volume_eur
    from {{ ref('stg_daily_crypto') }}
    where loaded_date = current_date
    group by coin_id, loaded_date
),

combined as (
    select * from legacy_seed
    union all
    select * from historical
    union all
    select * from derived_today
)

select
    coin_id,
    price_date,
    avg_price_eur,
    market_cap_eur,
    volume_eur
from combined
order by price_date desc, coin_id