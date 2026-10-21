select d.weekday_num, d.weekday_name, count(*) as orders
from fact_orders f join dim_date d using (date_key) where is_valid = 1 group by 1, 2 order by 1;
