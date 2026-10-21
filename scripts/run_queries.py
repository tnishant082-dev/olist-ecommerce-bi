"""Run every sql/queries/*.sql against the warehouse and save results to data/results."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]


def main():
    con = duckdb.connect(str(ROOT / "data" / "warehouse" / "olist.duckdb"), read_only=True)
    out = ROOT / "data" / "results"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / "sql" / "queries").glob("*.sql")):
        df = con.execute(f.read_text()).df()
        df.to_csv(out / f"{f.stem}.csv", index=False)
        print(f"\n-- {f.stem}\n{df.to_string(index=False)}")


if __name__ == "__main__":
    main()
