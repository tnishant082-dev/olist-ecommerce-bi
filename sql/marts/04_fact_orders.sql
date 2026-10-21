-- order grain fact. revenue = item price + freight (what the buyer paid for goods + shipping)
create or replace table fact_orders as
with items as (
    select order_id, count(*) as items, sum(price) as item_value, sum(freight) as freight_value,
           count(distinct seller_id) as sellers
    from stg_order_items group by 1
),
pay as (
    select order_id, sum(payment_value) as payment_value,
           arg_max(payment_type, payment_value) as main_payment_type,
           max(payment_installments) as installments
    from stg_payments group by 1
)
select o.order_id,
       c.customer_unique_id as customer_key,
       c.state as customer_state,
       cast(strftime(o.purchased_at, '%Y%m%d') as integer) as date_key,
       o.purchased_at,
       o.order_status,
       case when o.order_status in ('canceled', 'unavailable') then 0 else 1 end as is_valid,
       coalesce(i.items, 0) as items,
       coalesce(i.sellers, 0) as sellers,
       coalesce(i.item_value, 0) as item_value,
       coalesce(i.freight_value, 0) as freight_value,
       coalesce(i.item_value, 0) + coalesce(i.freight_value, 0) as order_value,
       p.payment_value,
       coalesce(p.main_payment_type, 'unknown') as payment_type,
       p.installments,
       case when o.delivered_at is not null then date_diff('day', o.purchased_at, o.delivered_at) end as delivery_days,
       date_diff('day', o.purchased_at, o.estimated_at) as promised_days,
       case when o.delivered_at is null then null
            when o.delivered_at::date > o.estimated_at::date then 1 else 0 end as is_late,
       r.review_score
from stg_orders o
join stg_customers c using (customer_id)
left join items i using (order_id)
left join pay p using (order_id)
left join stg_reviews r using (order_id);
