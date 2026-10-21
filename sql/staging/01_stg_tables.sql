-- staging layer: thin views over the cleaned parquet files
-- {clean} is replaced by scripts/build_warehouse.py with the data/clean path

create or replace view stg_orders as
select order_id, customer_id, order_status,
       order_purchase_timestamp      as purchased_at,
       order_approved_at             as approved_at,
       order_delivered_carrier_date  as shipped_at,
       order_delivered_customer_date as delivered_at,
       order_estimated_delivery_date as estimated_at
from read_parquet('{clean}/orders.parquet');

create or replace view stg_customers as
select customer_id, customer_unique_id, customer_zip_code_prefix as zip_prefix,
       customer_city as city, customer_state as state
from read_parquet('{clean}/customers.parquet');

create or replace view stg_order_items as
select order_id, order_item_id, product_id, seller_id, shipping_limit_date,
       price::decimal(12,2) as price, freight_value::decimal(12,2) as freight
from read_parquet('{clean}/order_items.parquet');

create or replace view stg_payments as
select order_id, payment_sequential, payment_type, payment_installments,
       payment_value::decimal(12,2) as payment_value
from read_parquet('{clean}/payments.parquet');

create or replace view stg_reviews as
select order_id, review_score, review_creation_date, review_answer_timestamp
from read_parquet('{clean}/reviews.parquet');

create or replace view stg_products as
select product_id, category, product_weight_g, product_photos_qty
from read_parquet('{clean}/products.parquet');

create or replace view stg_sellers as
select seller_id, seller_zip_code_prefix as zip_prefix, seller_city as city, seller_state as state
from read_parquet('{clean}/sellers.parquet');
