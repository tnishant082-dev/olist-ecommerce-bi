create or replace table dim_date as
with d as (
    select unnest(generate_series(date '2016-09-01', date '2018-10-31', interval 1 day))::date as dt
)
select cast(strftime(dt, '%Y%m%d') as integer) as date_key,
       dt as date,
       year(dt) as year,
       quarter(dt) as quarter,
       month(dt) as month,
       strftime(dt, '%b') as month_name,
       date_trunc('month', dt)::date as month_start,
       strftime(dt, '%Y-%m') as year_month,
       dayofweek(dt) as weekday_num,
       strftime(dt, '%a') as weekday_name,
       case when dayofweek(dt) in (0, 6) then 1 else 0 end as is_weekend
from d;
