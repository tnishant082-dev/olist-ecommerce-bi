"""Clean the raw Olist csvs with pandas and write typed files to data/clean.

What happens here:
- parse timestamps, trim/lowercase text keys
- translate product categories to english (two missing ones mapped by hand)
- drop the free text review title/message (portuguese text, not used)
- keep one review per order (latest answer wins)
- log row counts before/after into data/clean/cleaning_log.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "clean"

log = []


def note(table, step, before, after):
    log.append({"table": table, "step": step, "rows_before": before, "rows_after": after})


def read(name, **kw):
    return pd.read_csv(RAW / name, **kw)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # orders
    orders = read("olist_orders_dataset.csv")
    n = len(orders)
    ts_cols = [c for c in orders.columns if c.startswith("order_") and c not in ("order_id", "order_status")]
    for c in ts_cols:
        orders[c] = pd.to_datetime(orders[c], errors="coerce")
    orders = orders.drop_duplicates("order_id")
    note("orders", "dedupe order_id", n, len(orders))

    # customers
    cust = read("olist_customers_dataset.csv", dtype={"customer_zip_code_prefix": str})
    cust["customer_city"] = cust["customer_city"].str.strip().str.title()
    cust["customer_state"] = cust["customer_state"].str.strip().str.upper()
    note("customers", "load", len(cust), len(cust))

    # items
    items = read("olist_order_items_dataset.csv")
    n = len(items)
    items["shipping_limit_date"] = pd.to_datetime(items["shipping_limit_date"], errors="coerce")
    items = items[(items["price"] > 0)]
    note("order_items", "drop non-positive price", n, len(items))

    # payments
    pay = read("olist_order_payments_dataset.csv")
    n = len(pay)
    pay = pay[pay["payment_value"] > 0]
    note("payments", "drop zero value payments", n, len(pay))

    # reviews: drop text, keep latest answer per order
    rev = read("olist_order_reviews_dataset.csv",
               usecols=["review_id", "order_id", "review_score",
                        "review_creation_date", "review_answer_timestamp"])
    n = len(rev)
    rev["review_creation_date"] = pd.to_datetime(rev["review_creation_date"], errors="coerce")
    rev["review_answer_timestamp"] = pd.to_datetime(rev["review_answer_timestamp"], errors="coerce")
    rev = (rev.sort_values("review_answer_timestamp")
              .drop_duplicates("order_id", keep="last"))
    note("reviews", "one review per order", n, len(rev))

    # products + translation
    prod = read("olist_products_dataset.csv")
    prod = prod.rename(columns={"product_name_lenght": "product_name_length",
                                "product_description_lenght": "product_description_length"})
    tr = read("product_category_name_translation.csv")
    tr.columns = ["product_category_name", "category"]
    extra = pd.DataFrame({"product_category_name": ["pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"],
                          "category": ["pc_gamer", "portable_kitchen_appliances"]})
    tr = pd.concat([tr, extra]).drop_duplicates("product_category_name")
    prod = prod.merge(tr, on="product_category_name", how="left")
    prod["category"] = prod["category"].fillna("unknown").str.replace("_", " ")
    note("products", "translate category", len(prod), len(prod))

    sellers = read("olist_sellers_dataset.csv", dtype={"seller_zip_code_prefix": str})
    sellers["seller_city"] = sellers["seller_city"].str.strip().str.title()
    sellers["seller_state"] = sellers["seller_state"].str.strip().str.upper()
    note("sellers", "load", len(sellers), len(sellers))

    frames = {"orders": orders, "customers": cust, "order_items": items, "payments": pay,
              "reviews": rev, "products": prod, "sellers": sellers}
    for name, df in frames.items():
        df.to_parquet(OUT / f"{name}.parquet", index=False)
        print(f"{name:12s} {len(df):>8,d}")
    pd.DataFrame(log).to_csv(OUT / "cleaning_log.csv", index=False)


if __name__ == "__main__":
    main()
