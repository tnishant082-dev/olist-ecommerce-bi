select customer_type, count(*) as customers, round(count(*) / sum(count(*)) over (), 4) as share
from dim_customer where orders > 0 group by 1;
