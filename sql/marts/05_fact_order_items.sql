create or replace table fact_order_items as
select i.order_id, i.order_item_id, i.product_id as product_key, i.seller_id as seller_key,
       f.customer_key, f.date_key, f.order_status, f.is_valid,
       i.price, i.freight, i.price + i.freight as line_value,
       f.review_score, f.is_late,
       case when s.state = f.customer_state then 1 else 0 end as same_state
from stg_order_items i
join fact_orders f using (order_id)
left join stg_sellers s using (seller_id);
