-- rfm scored against the last purchase date in the data (2018-10-17) using quintiles
create or replace table mart_customer_rfm as
with base as (
    select customer_key,
           date_diff('day', max(purchased_at)::date, (select max(purchased_at)::date from fact_orders)) as recency_days,
           count(*) as frequency,
           sum(order_value) as monetary
    from fact_orders where is_valid = 1 group by 1
),
scored as (
    select *,
           6 - ntile(5) over (order by recency_days) as r,
           -- most customers have 1 order, so frequency is bucketed directly
           case when frequency >= 3 then 5 when frequency = 2 then 4 else 1 end as f,
           ntile(5) over (order by monetary) as m
    from base
)
select *, r::varchar || f::varchar || m::varchar as rfm_code,
       case when f >= 4 and r >= 4 then 'champions'
            when f >= 4 then 'loyal, slipping'
            when r >= 4 and m >= 4 then 'new big spenders'
            when r >= 4 then 'new low spenders'
            when r <= 2 and m >= 4 then 'lost big spenders'
            when r <= 2 then 'lost'
            else 'need attention' end as segment
from scored;

alter table dim_customer add column if not exists rfm_segment varchar;
update dim_customer d set rfm_segment = r.segment from mart_customer_rfm r where r.customer_key = d.customer_key;
update dim_customer set rfm_segment = 'no valid order' where rfm_segment is null;
