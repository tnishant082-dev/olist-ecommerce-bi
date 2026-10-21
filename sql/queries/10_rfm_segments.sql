select segment, count(*) as customers, round(sum(monetary), 2) as revenue,
       round(sum(monetary) / sum(sum(monetary)) over (), 4) as revenue_share,
       round(avg(recency_days), 0) as avg_recency_days
from mart_customer_rfm group by 1 order by revenue desc;
