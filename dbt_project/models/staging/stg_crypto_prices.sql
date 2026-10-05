with source as (
    select * from {{ source('raw', 'all_crypto_data') }}
),
cleaned as (
    select
        coin_id,
        price_date,
        price_eur,
        market_cap_eur,
        volume_eur,
        loaded_at
    from source
)

select * from cleaned