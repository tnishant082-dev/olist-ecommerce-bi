create or replace table dim_product as
select product_id as product_key, category,
       product_weight_g as weight_g, product_photos_qty as photos,
       case when product_weight_g is null then 'unknown'
            when product_weight_g < 500 then '< 0.5 kg'
            when product_weight_g < 2000 then '0.5-2 kg'
            when product_weight_g < 10000 then '2-10 kg'
            else '10 kg +' end as weight_band
from stg_products;

create or replace table dim_seller as
select seller_id as seller_key, city, state from stg_sellers;

create or replace table dim_state as
select * from (values
 ('AC','Acre','North'),('AL','Alagoas','Northeast'),('AP','Amapa','North'),('AM','Amazonas','North'),
 ('BA','Bahia','Northeast'),('CE','Ceara','Northeast'),('DF','Distrito Federal','Center-West'),
 ('ES','Espirito Santo','Southeast'),('GO','Goias','Center-West'),('MA','Maranhao','Northeast'),
 ('MT','Mato Grosso','Center-West'),('MS','Mato Grosso do Sul','Center-West'),('MG','Minas Gerais','Southeast'),
 ('PA','Para','North'),('PB','Paraiba','Northeast'),('PR','Parana','South'),('PE','Pernambuco','Northeast'),
 ('PI','Piaui','Northeast'),('RJ','Rio de Janeiro','Southeast'),('RN','Rio Grande do Norte','Northeast'),
 ('RS','Rio Grande do Sul','South'),('RO','Rondonia','North'),('RR','Roraima','North'),
 ('SC','Santa Catarina','South'),('SP','Sao Paulo','Southeast'),('SE','Sergipe','Northeast'),('TO','Tocantins','North')
) t(state, state_name, region);
