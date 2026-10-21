select count(*) as orders, count(distinct customer_key) as customers,
       round(sum(order_value), 2) as revenue, round(avg(order_value), 2) as aov,
       round(sum(freight_value) / sum(order_value), 4) as freight_share,
       round(avg(review_score), 3) as avg_review
from fact_orders where is_valid = 1;
