select payment_type, count(*) as orders, round(count(*) / sum(count(*)) over (), 4) as share,
       round(avg(order_value), 2) as aov, round(avg(installments), 2) as avg_installments
from fact_orders where is_valid = 1 group by 1 order by orders desc;
