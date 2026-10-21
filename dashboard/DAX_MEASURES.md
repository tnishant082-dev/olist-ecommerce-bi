# DAX measures

All measures live in the `_Measures` table of `dashboard/OlistCommerce.SemanticModel`. Valid order = status not `canceled` / `unavailable`. Money is BRL.


## Sales

**Revenue** - Item price + freight on valid orders, BRL
```dax
Revenue = CALCULATE ( SUM ( fact_orders[order_value] ), fact_orders[is_valid] = 1 )
```

**Item Revenue** - Item price only, line level
```dax
Item Revenue = CALCULATE ( SUM ( fact_order_items[price] ), fact_order_items[is_valid] = 1 )
```

**Freight**
```dax
Freight = CALCULATE ( SUM ( fact_orders[freight_value] ), fact_orders[is_valid] = 1 )
```

**Freight %** - Freight share of revenue
```dax
Freight % = DIVIDE ( [Freight], [Revenue] )
```

**Orders** - Orders not canceled or unavailable
```dax
Orders = CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_valid] = 1 )
```

**Items Sold**
```dax
Items Sold = CALCULATE ( COUNTROWS ( fact_order_items ), fact_order_items[is_valid] = 1 )
```

**AOV** - Average order value
```dax
AOV = DIVIDE ( [Revenue], [Orders] )
```

**Canceled %**
```dax
Canceled % = DIVIDE ( CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_valid] = 0 ), COUNTROWS ( fact_orders ) )
```


## Time intelligence

**Revenue PY**
```dax
Revenue PY = CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )
```

**Revenue YoY %**
```dax
Revenue YoY % = VAR py = [Revenue PY] RETURN IF ( NOT ISBLANK ( py ), DIVIDE ( [Revenue] - py, py ) )
```

**Revenue PM**
```dax
Revenue PM = CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )
```

**Revenue MoM %**
```dax
Revenue MoM % = VAR pm = [Revenue PM] RETURN IF ( NOT ISBLANK ( pm ), DIVIDE ( [Revenue] - pm, pm ) )
```

**Revenue YTD**
```dax
Revenue YTD = TOTALYTD ( [Revenue], dim_date[date] )
```

**Revenue Running Total** - Cumulative revenue since first order
```dax
Revenue Running Total = VAR d = MAX ( dim_date[date] ) RETURN CALCULATE ( [Revenue], dim_date[date] <= d, ALL ( dim_date ) )
```

**Revenue 3M Rolling**
```dax
Revenue 3M Rolling = CALCULATE ( [Revenue], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )
```

**Orders PY**
```dax
Orders PY = CALCULATE ( [Orders], SAMEPERIODLASTYEAR ( dim_date[date] ) )
```

**Orders YoY %**
```dax
Orders YoY % = VAR py = [Orders PY] RETURN IF ( NOT ISBLANK ( py ), DIVIDE ( [Orders] - py, py ) )
```


## Customers

**Customers** - Distinct customer_unique_id with a valid order
```dax
Customers = CALCULATE ( DISTINCTCOUNT ( fact_orders[customer_key] ), fact_orders[is_valid] = 1 )
```

**New Customers** - Customers whose first valid order falls in the period
```dax
New Customers = VAR mn = MIN ( dim_date[date] ) VAR mx = MAX ( dim_date[date] ) RETURN CALCULATE ( [Customers], FILTER ( dim_customer, dim_customer[first_order_date] >= mn && dim_customer[first_order_date] <= mx ) )
```

**Returning Customers**
```dax
Returning Customers = [Customers] - [New Customers]
```

**Repeat Customer %** - Share of customers with 2+ valid orders overall
```dax
Repeat Customer % = DIVIDE ( CALCULATE ( [Customers], dim_customer[orders] > 1 ), [Customers] )
```

**Revenue per Customer**
```dax
Revenue per Customer = DIVIDE ( [Revenue], [Customers] )
```

**Cohort Size**
```dax
Cohort Size = SUM ( mart_cohort_retention[cohort_size] )
```

**Cohort Active Customers**
```dax
Cohort Active Customers = SUM ( mart_cohort_retention[customers] )
```

**Cohort Retention %** - Share of a cohort buying again n months after first order
```dax
Cohort Retention % = DIVIDE ( [Cohort Active Customers], [Cohort Size] )
```

**RFM Revenue Share**
```dax
RFM Revenue Share = DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( dim_customer[rfm_segment] ) ) )
```

**Avg Recency Days** - Days since last order, measured from the last purchase date in the data
```dax
Avg Recency Days = AVERAGEX ( VALUES ( dim_customer[customer_key] ), DATEDIFF ( CALCULATE ( MAX ( dim_customer[last_order_date] ) ), DATE ( 2018, 10, 17 ), DAY ) )
```


## Delivery

**Avg Delivery Days**
```dax
Avg Delivery Days = CALCULATE ( AVERAGE ( fact_orders[delivery_days] ), fact_orders[order_status] = "delivered" )
```

**Late Delivery %** - Delivered after the estimated date
```dax
Late Delivery % = CALCULATE ( AVERAGE ( fact_orders[is_late] ), fact_orders[order_status] = "delivered" )
```

**Avg Review**
```dax
Avg Review = AVERAGE ( fact_orders[review_score] )
```

**Low Review %** - Share of reviews scoring 1 or 2
```dax
Low Review % = DIVIDE ( CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[review_score] <= 2 ), CALCULATE ( COUNTROWS ( fact_orders ), NOT ISBLANK ( fact_orders[review_score] ) ) )
```


## Products

**Sellers**
```dax
Sellers = CALCULATE ( DISTINCTCOUNT ( fact_order_items[seller_key] ), fact_order_items[is_valid] = 1 )
```

**Revenue per Seller**
```dax
Revenue per Seller = DIVIDE ( [Item Revenue], [Sellers] )
```

**Category Share**
```dax
Category Share = DIVIDE ( [Item Revenue], CALCULATE ( [Item Revenue], ALL ( dim_product[category] ) ) )
```

**Category Rank**
```dax
Category Rank = IF ( HASONEVALUE ( dim_product[category] ), RANKX ( ALL ( dim_product[category] ), [Item Revenue] ) )
```

**Cross-state Line %** - Lines shipped from a seller in another state
```dax
Cross-state Line % = DIVIDE ( CALCULATE ( [Items Sold], fact_order_items[same_state] = 0 ), [Items Sold] )
```

## Checking the numbers

`data/results/14_expected_measures.csv` has the same figures computed in SQL. After the first refresh, the Overview cards with no slicer set should match the `(all)` rows. Note `Avg Review` on the report is over all orders with a review (4.07), while the SQL headline query uses valid orders only (4.10).
