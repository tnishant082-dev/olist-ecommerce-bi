"""Build the DuckDB warehouse from data/clean and export star schema tables.

steps: sql/staging -> sql/marts -> sql/checks (fails loudly) -> data/powerbi parquet files
"""
from pathlib import Path
import sys
import duckdb

ROOT = Path(__file__).resolve().parents[1]
CLEAN = (ROOT / "data" / "clean").as_posix()
DB = ROOT / "data" / "warehouse" / "olist.duckdb"
PBI = ROOT / "data" / "powerbi"

EXPORT = ["dim_date", "dim_customer", "dim_product", "dim_seller", "dim_state",
          "fact_orders", "fact_order_items", "mart_cohort_retention", "mart_monthly"]


def run_folder(con, folder):
    for f in sorted((ROOT / "sql" / folder).glob("*.sql")):
        print("run", f.relative_to(ROOT))
        con.execute(f.read_text().replace("{clean}", CLEAN))


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    PBI.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = duckdb.connect(str(DB))
    run_folder(con, "staging")
    run_folder(con, "marts")

    checks = con.execute((ROOT / "sql" / "checks" / "data_quality.sql").read_text()).fetchall()
    failed = 0
    with open(ROOT / "data" / "results" / "data_quality.csv", "w") as fh:
        fh.write("check_name,bad_rows,status\n")
        for name, bad in checks:
            # checks named "warn: ..." are known source quirks, reported but not fatal
            if bad == 0:
                status = "pass"
            elif name.startswith("warn:"):
                status = "warn"
            else:
                status = "FAIL"
                failed += 1
            print(f"  {status:4s} {bad:>6d}  {name}")
            fh.write(f"{name},{bad},{status}\n")

    for t in EXPORT:
        out = (PBI / f"{t}.parquet").as_posix()
        # decimals go out as double, power query reads those without fuss
        cols = con.execute(f"describe {t}").fetchall()
        sel = ", ".join(f"{c[0]}::double as {c[0]}" if c[1].startswith("DECIMAL") else c[0] for c in cols)
        con.execute(f"copy (select {sel} from {t}) to '{out}' (format parquet, compression zstd)")
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"export {t:24s} {n:>8,d}")
    con.close()
    if failed:
        print(f"{failed} data quality checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
