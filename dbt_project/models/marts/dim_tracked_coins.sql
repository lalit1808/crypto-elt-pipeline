with latest_snapshot as (
    select max(snapshot_at) as latest_snapshot_at
    from {{ source('raw', 'daily_crypto') }}
)

select distinct d.coin_id
from {{ source('raw', 'daily_crypto') }} d
inner join latest_snapshot l on d.snapshot_at = l.latest_snapshot_at
where d.market_cap_rank <= 25