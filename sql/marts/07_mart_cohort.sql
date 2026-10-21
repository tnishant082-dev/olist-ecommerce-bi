-- monthly acquisition cohorts and the share of each cohort that buys again in month n
create or replace table mart_cohort_retention as
with o as (
    select f.customer_key, d.cohort_month, date_trunc('month', f.purchased_at)::date as order_month
    from fact_orders f join dim_customer d using (customer_key)
    where f.is_valid = 1
),
x as (
    select cohort_month,
           date_diff('month', cohort_month, order_month) as month_n,
           count(distinct customer_key) as customers
    from o group by 1, 2
)
select x.cohort_month, x.month_n, x.customers,
       first_value(x.customers) over (partition by x.cohort_month order by x.month_n) as cohort_size,
       round(x.customers / first_value(x.customers) over (partition by x.cohort_month order by x.month_n), 4) as retention
from x
where x.cohort_month between date '2017-01-01' and date '2018-08-01'
order by 1, 2;

create or replace table mart_monthly as
select date_trunc('month', purchased_at)::date as month,
       count(*) as orders,
       count(distinct customer_key) as customers,
       sum(order_value) as revenue,
       sum(freight_value) as freight,
       avg(order_value) as aov,
       avg(review_score) as avg_review,
       avg(is_late) as late_rate
from fact_orders where is_valid = 1
group by 1 order by 1;
