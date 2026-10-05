with ranked_snapshots as (
    select
        coin_id,
        price_eur,
        snapshot_at,
        row_number() over (partition by coin_id order by snapshot_at desc) as rn
    from {{ ref('stg_daily_crypto') }}
    where loaded_date = current_date
),

latest_two as (
    select
        coin_id,
        max(case when rn = 1 then price_eur end) as current_price_eur,
        max(case when rn = 2 then price_eur end) as previous_price_eur,
        max(case when rn = 1 then snapshot_at end) as current_snapshot_at,
        max(case when rn = 2 then snapshot_at end) as previous_snapshot_at
    from ranked_snapshots
    where rn <= 2
    group by coin_id
),

with_change as (
    select
        coin_id,
        current_snapshot_at,
        previous_snapshot_at,
        previous_price_eur,
        current_price_eur,
        round(
            (current_price_eur - previous_price_eur) / previous_price_eur * 100,
            2
        ) as pct_change
    from latest_two
    where previous_price_eur is not null
)

select
    coin_id,
    current_snapshot_at,
    previous_snapshot_at,
    previous_price_eur,
    current_price_eur,
    pct_change,
    rank() over (order by pct_change desc) as gainer_rank,
    rank() over (order by pct_change asc) as loser_rank
from with_change
order by pct_change desc
