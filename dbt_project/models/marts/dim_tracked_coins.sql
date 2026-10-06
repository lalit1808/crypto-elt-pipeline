with latest_snapshot as (
    select max(snapshot_at) as latest_snapshot_at
    from {{ ref('stg_daily_crypto') }}
)

select distinct d.coin_id
from {{ ref('stg_daily_crypto') }} d
inner join latest_snapshot l on d.snapshot_at = l.latest_snapshot_at
