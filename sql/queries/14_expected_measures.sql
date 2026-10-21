-- reference values to check the DAX measures against after the first refresh in desktop
select 'Revenue (all)' as measure, round(sum(order_value), 2) as value from fact_orders where is_valid = 1
union all select 'Orders (all)', count(*) from fact_orders where is_valid = 1
union all select 'Customers (all)', count(distinct customer_key) from fact_orders where is_valid = 1
union all select 'AOV (all)', round(avg(order_value), 2) from fact_orders where is_valid = 1
union all select 'Item Revenue (all)', round(sum(price), 2) from fact_order_items where is_valid = 1
union all select 'Revenue 2017', round(sum(order_value), 2) from fact_orders where is_valid = 1 and year(purchased_at) = 2017
union all select 'Revenue 2018', round(sum(order_value), 2) from fact_orders where is_valid = 1 and year(purchased_at) = 2018
union all select 'Revenue Nov 2017', round(sum(order_value), 2) from fact_orders where is_valid = 1 and strftime(purchased_at, '%Y-%m') = '2017-11'
union all select 'Revenue MoM % Nov 2017', round(
    (select sum(order_value) from fact_orders where is_valid = 1 and strftime(purchased_at, '%Y-%m') = '2017-11') /
    (select sum(order_value) from fact_orders where is_valid = 1 and strftime(purchased_at, '%Y-%m') = '2017-10') - 1, 4)
union all select 'Revenue YoY % Aug 2018', round(
    (select sum(order_value) from fact_orders where is_valid = 1 and strftime(purchased_at, '%Y-%m') = '2018-08') /
    (select sum(order_value) from fact_orders where is_valid = 1 and strftime(purchased_at, '%Y-%m') = '2017-08') - 1, 4)
union all select 'Late Delivery % (all)', round(avg(is_late), 4) from fact_orders where order_status = 'delivered'
union all select 'Avg Review (all)', round(avg(review_score), 3) from fact_orders
union all select 'Repeat Customer % (all)', round(avg(case when orders > 1 then 1.0 else 0 end), 4) from dim_customer where orders > 0;
