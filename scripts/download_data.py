"""Fetch the Olist Brazilian e-commerce csvs into data/raw.

Source: Kaggle "Brazilian E-Commerce Public Dataset by Olist" (CC BY-NC-SA 4.0).
The files are pulled from a public GitHub mirror of the Kaggle release so no
Kaggle login is needed. If the mirror goes away, download the zip from Kaggle
and unpack it into data/raw.
"""
from pathlib import Path
import urllib.request

BASE = "https://raw.githubusercontent.com/mara/mara-olist-ecommerce-data/master/data/olist-ecommerce/"
FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        out = RAW / name
        if out.exists() and out.stat().st_size > 0:
            print("have", name)
            continue
        print("get ", name)
        urllib.request.urlretrieve(BASE + name, out)


if __name__ == "__main__":
    main()
