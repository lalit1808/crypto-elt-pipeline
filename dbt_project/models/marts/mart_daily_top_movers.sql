select
    coin_id,
    price_date,
    open_price_eur,
    close_price_eur,
    movement_pct_of_the_day as pct_change,
    rank() over (partition by price_date order by movement_pct_of_the_day desc) as gainer_rank,
    rank() over (partition by price_date order by movement_pct_of_the_day asc) as loser_rank
from {{ ref('fact_daily_price_summary') }}
order by price_date desc, pct_change desc