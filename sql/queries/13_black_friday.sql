select f.date_key, count(*) as orders, round(sum(order_value), 2) as revenue
from fact_orders f where is_valid = 1 group by 1 order by orders desc limit 5;
