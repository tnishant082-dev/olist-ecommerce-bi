with s as (select seller_key, sum(price) as rev from fact_order_items where is_valid = 1 group by 1),
r as (select *, row_number() over (order by rev desc) as rk, count(*) over () as n from s)
select count(*) filter (where rk <= n * 0.1) as top10pct_sellers, max(n) as sellers,
       round(sum(rev) filter (where rk <= n * 0.1) / sum(rev), 4) as top10pct_share
from r;
