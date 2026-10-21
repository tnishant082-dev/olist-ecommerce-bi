select f.customer_state as state, s.region, count(*) as orders, round(sum(order_value), 2) as revenue,
       round(sum(order_value) / sum(sum(order_value)) over (), 4) as share,
       round(avg(delivery_days), 1) as avg_delivery_days, round(avg(freight_value / nullif(order_value, 0)), 4) as freight_share
from fact_orders f join dim_state s on s.state = f.customer_state
where is_valid = 1 group by 1, 2 order by revenue desc;
