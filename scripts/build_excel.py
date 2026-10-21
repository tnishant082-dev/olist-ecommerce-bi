"""Excel summary workbook from the warehouse: excel/olist_summary.xlsx"""
from pathlib import Path
import duckdb
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import LineChart, BarChart, Reference

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "excel" / "olist_summary.xlsx"
HEAD = PatternFill("solid", fgColor="1F4E78")


def q(con, name):
    return con.execute((ROOT / "sql" / "queries" / f"{name}.sql").read_text()).df()


def main():
    con = duckdb.connect(str(ROOT / "data" / "warehouse" / "olist.duckdb"), read_only=True)
    kpi = q(con, "01_headline_kpis").T.reset_index()
    kpi.columns = ["metric", "value"]
    monthly = q(con, "03_monthly_trend")
    cats = q(con, "06_top_categories")
    states = q(con, "07_state_revenue")
    rfm = q(con, "10_rfm_segments")
    pay = q(con, "09_payment_mix")
    late = q(con, "08_late_vs_review")
    coh = con.execute("select strftime(cohort_month, '%Y-%m') as cohort, month_n, retention from mart_cohort_retention where month_n <= 12").df()
    coh = coh.pivot(index="cohort", columns="month_n", values="retention").reset_index()
    coh.columns = ["cohort"] + [f"m{c}" for c in coh.columns[1:]]
    dq = pd.read_csv(ROOT / "data" / "results" / "data_quality.csv")
    con.close()

    OUT.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        notes = pd.DataFrame({"notes": [
            "Olist Brazilian e-commerce, orders 2016-09 to 2018-10 (Kaggle, CC BY-NC-SA 4.0)",
            "Revenue = item price + freight for orders not canceled/unavailable, in BRL",
            "Monthly sheet covers Jan 2017 - Aug 2018 (complete months only)",
            "MoM % column on Monthly is an Excel formula, the rest are values from the warehouse",
        ]})
        notes.to_excel(xw, sheet_name="About", index=False)
        kpi.to_excel(xw, sheet_name="KPIs", index=False)
        monthly.to_excel(xw, sheet_name="Monthly", index=False)
        cats.to_excel(xw, sheet_name="Top categories", index=False)
        states.to_excel(xw, sheet_name="States", index=False)
        rfm.to_excel(xw, sheet_name="RFM", index=False)
        pay.to_excel(xw, sheet_name="Payments", index=False)
        late.to_excel(xw, sheet_name="Late vs review", index=False)
        coh.to_excel(xw, sheet_name="Cohorts", index=False)
        dq.to_excel(xw, sheet_name="Data quality", index=False)

    wb = load_workbook(OUT)
    for ws in wb.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HEAD
            c.alignment = Alignment(horizontal="center")
        for col in ws.columns:
            width = max(len(str(c.value or "")) for c in col) + 2
            ws.column_dimensions[col[0].column_letter].width = min(width, 70)
        ws.freeze_panes = "A2"

    ws = wb["Monthly"]
    n = ws.max_row
    ws.cell(1, 7, "revenue MoM %").font = Font(bold=True, color="FFFFFF")
    ws.cell(1, 7).fill = HEAD
    for r in range(3, n + 1):
        ws.cell(r, 7, f"=C{r}/C{r-1}-1").number_format = "0.0%"
    ws.cell(1, 8, "running revenue").font = Font(bold=True, color="FFFFFF")
    ws.cell(1, 8).fill = HEAD
    for r in range(2, n + 1):
        ws.cell(r, 8, f"=SUM($C$2:C{r})").number_format = "#,##0"
    for r in range(2, n + 1):
        ws.cell(r, 3).number_format = "#,##0"
        ws.cell(r, 5).number_format = "0.0%"
    ch = LineChart()
    ch.title = "Monthly revenue (BRL)"
    ch.add_data(Reference(ws, min_col=3, min_row=1, max_row=n), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=n))
    ch.width, ch.height = 22, 9
    ws.add_chart(ch, "J2")

    ws = wb["Top categories"]
    bc = BarChart()
    bc.type = "bar"
    bc.title = "Item revenue by category"
    bc.add_data(Reference(ws, min_col=3, min_row=1, max_row=ws.max_row), titles_from_data=True)
    bc.set_categories(Reference(ws, min_col=1, min_row=2, max_row=ws.max_row))
    bc.width, bc.height = 18, 9
    ws.add_chart(bc, "G2")

    ws = wb["Cohorts"]
    rng = f"B2:{ws.cell(ws.max_row, ws.max_column).coordinate}"
    ws.conditional_formatting.add(rng, ColorScaleRule(start_type="min", start_color="FFFFFF",
                                                      end_type="max", end_color="2E75B6"))
    for row in ws.iter_rows(min_row=2, min_col=2):
        for c in row:
            c.number_format = "0.00%"
    wb.save(OUT)
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
