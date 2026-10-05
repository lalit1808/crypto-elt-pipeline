with source as (
    select * from {{ source('raw', 'daily_crypto') }}
),

cleaned as (
    select
        coin_id,
        price_eur,
        market_cap_eur,
        market_cap_rank,
        volume_eur,
        price_change_pct_24h,
        snapshot_at,
        loaded_date
    from source
)

select * from cleaned