-- one row per real person (customer_unique_id); olist issues a new customer_id per order.
-- counts and cohort use valid (not canceled/unavailable) orders only
create or replace table dim_customer as
with o as (
    select c.customer_unique_id, o.order_id, o.purchased_at, c.city, c.state,
           o.order_status not in ('canceled', 'unavailable') as valid
    from stg_orders o join stg_customers c using (customer_id)
),
last_geo as (
    select customer_unique_id, arg_max(city, purchased_at) as city, arg_max(state, purchased_at) as state
    from o group by 1
),
agg as (
    select customer_unique_id,
           coalesce(min(purchased_at) filter (where valid), min(purchased_at))::date as first_order_date,
           max(purchased_at)::date as last_order_date,
           count(distinct order_id) filter (where valid) as orders
    from o group by 1
)
select a.customer_unique_id as customer_key, g.city, g.state,
       a.first_order_date, a.last_order_date, a.orders,
       date_trunc('month', a.first_order_date)::date as cohort_month,
       case when a.orders > 1 then 'repeat' else 'one-time' end as customer_type
from agg a join last_geo g using (customer_unique_id);
