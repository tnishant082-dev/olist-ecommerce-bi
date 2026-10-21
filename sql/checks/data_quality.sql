-- each check returns one row: name and number of offending rows. 0 = pass
select 'fact_orders duplicate order_id' as check_name, count(*) - count(distinct order_id) as bad from fact_orders
union all select 'fact_order_items duplicate line', count(*) - count(distinct (order_id, order_item_id)) from fact_order_items
union all select 'items without product in dim_product', count(*) from fact_order_items i left join dim_product p using (product_key) where p.product_key is null
union all select 'items without seller in dim_seller', count(*) from fact_order_items i left join dim_seller s using (seller_key) where s.seller_key is null
union all select 'orders without date in dim_date', count(*) from fact_orders f left join dim_date d using (date_key) where d.date_key is null
union all select 'orders without customer in dim_customer', count(*) from fact_orders f left join dim_customer c using (customer_key) where c.customer_key is null
union all select 'negative order value', count(*) from fact_orders where order_value < 0
union all select 'review score outside 1-5', count(*) from fact_orders where review_score not between 1 and 5
union all select 'delivered before purchase', count(*) from fact_orders where delivery_days < 0
union all select 'customer state not in dim_state', count(*) from dim_customer c left join dim_state s using (state) where s.state is null
union all select 'seller state not in dim_state', count(*) from dim_seller c left join dim_state s using (state) where s.state is null
-- payment vs items+freight: olist adds interest on installments, so only flag big gaps
union all select 'warn: valid orders with payment gap > 5 BRL', count(*) from fact_orders where is_valid = 1 and items > 0 and abs(payment_value - order_value) > 5 and installments <= 1;
