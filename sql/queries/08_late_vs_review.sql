select case is_late when 1 then 'late' else 'on time' end as delivery, count(*) as orders,
       round(avg(review_score), 3) as avg_review,
       round(avg(case when review_score <= 2 then 1.0 else 0 end), 4) as low_review_rate
from fact_orders where order_status = 'delivered' and is_late is not null group by 1;
