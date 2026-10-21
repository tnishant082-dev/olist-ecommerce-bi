-- jan-aug only so 2017 and 2018 are like for like
select year(purchased_at) as year, count(*) as orders, round(sum(order_value), 2) as revenue
from fact_orders where is_valid = 1 and month(purchased_at) <= 8 and year(purchased_at) in (2017, 2018)
group by 1 order by 1;
