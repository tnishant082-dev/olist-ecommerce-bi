"""Static matplotlib charts from the warehouse (screenshots/charts).

These are python charts of the same marts, not Power BI screenshots.
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots" / "charts"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "warehouse" / "olist.duckdb"), read_only=True)

    m = con.execute("select month, revenue, orders, late_rate, avg_review from mart_monthly "
                    "where month between date '2017-01-01' and date '2018-08-01' order by 1").df()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(m["month"], m["revenue"] / 1e6, marker="o")
    ax.set_title("Monthly revenue, BRL millions (valid orders, Jan 2017 - Aug 2018)")
    ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "01-monthly-revenue.png", dpi=120); plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.bar(m["month"], m["late_rate"] * 100, width=20, color="#E15759", alpha=.7, label="late %")
    ax1.set_ylabel("late deliveries %")
    ax2 = ax1.twinx()
    ax2.plot(m["month"], m["avg_review"], color="#0B5CAD", marker="o", label="avg review")
    ax2.set_ylabel("avg review score")
    ax1.set_title("Late delivery share vs average review score by purchase month")
    fig.tight_layout(); fig.savefig(OUT / "02-late-vs-review.png", dpi=120); plt.close(fig)

    c = con.execute((ROOT / "sql/queries/06_top_categories.sql").read_text()).df().iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(c["category"], c["item_revenue"] / 1e6, color="#0B5CAD")
    ax.set_title("Top 10 categories by item revenue, BRL millions")
    fig.tight_layout(); fig.savefig(OUT / "03-top-categories.png", dpi=120); plt.close(fig)

    s = con.execute((ROOT / "sql/queries/07_state_revenue.sql").read_text()).df()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(s["avg_delivery_days"], s["freight_share"] * 100, s=s["orders"] / 60, alpha=.6)
    for _, r in s.iterrows():
        ax.annotate(r["state"], (r["avg_delivery_days"], r["freight_share"] * 100), fontsize=8)
    ax.set_xlabel("avg delivery days"); ax.set_ylabel("freight % of order value")
    ax.set_title("Customer state: delivery time vs freight share (bubble = orders)")
    fig.tight_layout(); fig.savefig(OUT / "04-state-delivery-freight.png", dpi=120); plt.close(fig)

    h = con.execute("select strftime(cohort_month, '%Y-%m') c, month_n, retention from mart_cohort_retention "
                    "where month_n between 1 and 12").df().pivot(index="c", columns="month_n", values="retention")
    fig, ax = plt.subplots(figsize=(11, 7))
    im = ax.imshow(h.values * 100, cmap="Blues", aspect="auto")
    ax.set_yticks(range(len(h.index)), h.index); ax.set_xticks(range(len(h.columns)), h.columns)
    ax.set_xlabel("months after first order"); ax.set_title("Cohort retention %, months 1-12")
    fig.colorbar(im)
    fig.tight_layout(); fig.savefig(OUT / "05-cohort-retention.png", dpi=120); plt.close(fig)
    print("charts in", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
