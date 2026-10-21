select p.category, count(distinct i.order_id) as orders, round(sum(i.price), 2) as item_revenue,
       round(sum(i.price) / sum(sum(i.price)) over (), 4) as share
from fact_order_items i join dim_product p using (product_key)
where i.is_valid = 1 group by 1 order by item_revenue desc limit 10;
