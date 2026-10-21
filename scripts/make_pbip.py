"""Write the Power BI project (PBIP) under dashboard/.

The semantic model (TMDL) and report pages (PBIR json) are kept in this one
script so names stay in sync. Ids/lineage tags are uuid5 so reruns give the
same files and git diffs stay small. Open dashboard/OlistCommerce.pbip in
Power BI Desktop (Mar 2024 or newer, PBIR + TMDL preview features on).
"""
from pathlib import Path
import json
import shutil
import uuid

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
NAME = "OlistCommerce"
PBI_DATA = ROOT / "data" / "powerbi"
NS = uuid.UUID("6f1b6c2e-2b41-4c55-9e0e-0b3b0c1a7d10")


def tag(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def wjson(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- model

TABLES = {
    "fact_orders": "Order grain fact, one row per olist order",
    "fact_order_items": "Order line grain fact (product x seller)",
    "dim_date": "Calendar 2016-09-01 to 2018-10-31",
    "dim_customer": "One row per customer_unique_id with cohort and RFM segment",
    "dim_product": "Products with english category",
    "dim_seller": "Marketplace sellers",
    "dim_state": "Brazilian states and regions (customer side)",
    "mart_cohort_retention": "Monthly acquisition cohorts from SQL mart",
}

HIDDEN = {"order_id", "customer_key", "product_key", "seller_key", "date_key", "customer_state"}

DTYPE = {"VARCHAR": ("string", None, "type text"),
         "INTEGER": ("int64", "0", "Int64.Type"),
         "BIGINT": ("int64", "0", "Int64.Type"),
         "DOUBLE": ("double", "#,0.00", "type number"),
         "DATE": ("dateTime", "yyyy-mm-dd", "type date"),
         "TIMESTAMP": ("dateTime", "yyyy-mm-dd hh:nn", "type datetime")}

RELS = [
    ("fact_orders", "date_key", "dim_date", "date_key"),
    ("fact_orders", "customer_key", "dim_customer", "customer_key"),
    ("fact_orders", "customer_state", "dim_state", "state"),
    ("fact_order_items", "date_key", "dim_date", "date_key"),
    ("fact_order_items", "customer_key", "dim_customer", "customer_key"),
    ("fact_order_items", "product_key", "dim_product", "product_key"),
    ("fact_order_items", "seller_key", "dim_seller", "seller_key"),
]

SORT_BY = {("dim_date", "month_name"): "month", ("dim_date", "weekday_name"): "weekday_num"}

# (folder, name, expression, format, description)
MEASURES = [
    ("Sales", "Revenue", "CALCULATE ( SUM ( fact_orders[order_value] ), fact_orders[is_valid] = 1 )", "\\R\\$ #,0", "Item price + freight on valid orders, BRL"),
    ("Sales", "Item Revenue", "CALCULATE ( SUM ( fact_order_items[price] ), fact_order_items[is_valid] = 1 )", "\\R\\$ #,0", "Item price only, line level"),
    ("Sales", "Freight", "CALCULATE ( SUM ( fact_orders[freight_value] ), fact_orders[is_valid] = 1 )", "\\R\\$ #,0", None),
    ("Sales", "Freight %", "DIVIDE ( [Freight], [Revenue] )", "0.0%", "Freight share of revenue"),
    ("Sales", "Orders", "CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_valid] = 1 )", "#,0", "Orders not canceled or unavailable"),
    ("Sales", "Items Sold", "CALCULATE ( COUNTROWS ( fact_order_items ), fact_order_items[is_valid] = 1 )", "#,0", None),
    ("Sales", "AOV", "DIVIDE ( [Revenue], [Orders] )", "\\R\\$ #,0.00", "Average order value"),
    ("Sales", "Canceled %", "DIVIDE ( CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[is_valid] = 0 ), COUNTROWS ( fact_orders ) )", "0.00%", None),
    ("Time intelligence", "Revenue PY", "CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )", "\\R\\$ #,0", None),
    ("Time intelligence", "Revenue YoY %", "VAR py = [Revenue PY] RETURN IF ( NOT ISBLANK ( py ), DIVIDE ( [Revenue] - py, py ) )", "+0.0%;-0.0%;0.0%", None),
    ("Time intelligence", "Revenue PM", "CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )", "\\R\\$ #,0", None),
    ("Time intelligence", "Revenue MoM %", "VAR pm = [Revenue PM] RETURN IF ( NOT ISBLANK ( pm ), DIVIDE ( [Revenue] - pm, pm ) )", "+0.0%;-0.0%;0.0%", None),
    ("Time intelligence", "Revenue YTD", "TOTALYTD ( [Revenue], dim_date[date] )", "\\R\\$ #,0", None),
    ("Time intelligence", "Revenue Running Total", "VAR d = MAX ( dim_date[date] ) RETURN CALCULATE ( [Revenue], dim_date[date] <= d, ALL ( dim_date ) )", "\\R\\$ #,0", "Cumulative revenue since first order"),
    ("Time intelligence", "Revenue 3M Rolling", "CALCULATE ( [Revenue], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) )", "\\R\\$ #,0", None),
    ("Time intelligence", "Orders PY", "CALCULATE ( [Orders], SAMEPERIODLASTYEAR ( dim_date[date] ) )", "#,0", None),
    ("Time intelligence", "Orders YoY %", "VAR py = [Orders PY] RETURN IF ( NOT ISBLANK ( py ), DIVIDE ( [Orders] - py, py ) )", "+0.0%;-0.0%;0.0%", None),
    ("Customers", "Customers", "CALCULATE ( DISTINCTCOUNT ( fact_orders[customer_key] ), fact_orders[is_valid] = 1 )", "#,0", "Distinct customer_unique_id with a valid order"),
    ("Customers", "New Customers", "VAR mn = MIN ( dim_date[date] ) VAR mx = MAX ( dim_date[date] ) RETURN CALCULATE ( [Customers], FILTER ( dim_customer, dim_customer[first_order_date] >= mn && dim_customer[first_order_date] <= mx ) )", "#,0", "Customers whose first valid order falls in the period"),
    ("Customers", "Returning Customers", "[Customers] - [New Customers]", "#,0", None),
    ("Customers", "Repeat Customer %", "DIVIDE ( CALCULATE ( [Customers], dim_customer[orders] > 1 ), [Customers] )", "0.00%", "Share of customers with 2+ valid orders overall"),
    ("Customers", "Revenue per Customer", "DIVIDE ( [Revenue], [Customers] )", "\\R\\$ #,0.00", None),
    ("Customers", "Cohort Size", "SUM ( mart_cohort_retention[cohort_size] )", "#,0", None),
    ("Customers", "Cohort Active Customers", "SUM ( mart_cohort_retention[customers] )", "#,0", None),
    ("Customers", "Cohort Retention %", "DIVIDE ( [Cohort Active Customers], [Cohort Size] )", "0.00%", "Share of a cohort buying again n months after first order"),
    ("Customers", "RFM Revenue Share", "DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( dim_customer[rfm_segment] ) ) )", "0.0%", None),
    ("Customers", "Avg Recency Days", "AVERAGEX ( VALUES ( dim_customer[customer_key] ), DATEDIFF ( CALCULATE ( MAX ( dim_customer[last_order_date] ) ), DATE ( 2018, 10, 17 ), DAY ) )", "#,0", "Days since last order, measured from the last purchase date in the data"),
    ("Delivery", "Avg Delivery Days", "CALCULATE ( AVERAGE ( fact_orders[delivery_days] ), fact_orders[order_status] = \"delivered\" )", "0.0", None),
    ("Delivery", "Late Delivery %", "CALCULATE ( AVERAGE ( fact_orders[is_late] ), fact_orders[order_status] = \"delivered\" )", "0.0%", "Delivered after the estimated date"),
    ("Delivery", "Avg Review", "AVERAGE ( fact_orders[review_score] )", "0.00", None),
    ("Delivery", "Low Review %", "DIVIDE ( CALCULATE ( COUNTROWS ( fact_orders ), fact_orders[review_score] <= 2 ), CALCULATE ( COUNTROWS ( fact_orders ), NOT ISBLANK ( fact_orders[review_score] ) ) )", "0.0%", "Share of reviews scoring 1 or 2"),
    ("Products", "Sellers", "CALCULATE ( DISTINCTCOUNT ( fact_order_items[seller_key] ), fact_order_items[is_valid] = 1 )", "#,0", None),
    ("Products", "Revenue per Seller", "DIVIDE ( [Item Revenue], [Sellers] )", "\\R\\$ #,0", None),
    ("Products", "Category Share", "DIVIDE ( [Item Revenue], CALCULATE ( [Item Revenue], ALL ( dim_product[category] ) ) )", "0.0%", None),
    ("Products", "Category Rank", "IF ( HASONEVALUE ( dim_product[category] ), RANKX ( ALL ( dim_product[category] ), [Item Revenue] ) )", "0", None),
    ("Products", "Cross-state Line %", "DIVIDE ( CALCULATE ( [Items Sold], fact_order_items[same_state] = 0 ), [Items Sold] )", "0.0%", "Lines shipped from a seller in another state"),
]


def tmdl_table(con, name):
    cols = con.execute(f"describe select * from '{(PBI_DATA / (name + '.parquet')).as_posix()}'").fetchall()
    lines = [f"/// {TABLES[name]}", f"table {name}", f"\tlineageTag: {tag('t', name)}"]
    if name == "dim_date":
        lines.append("\tdataCategory: Time")
    lines.append("")
    typed = []
    for c, t, *_ in cols:
        dt, fmt, mtype = DTYPE[t]
        if c in ("order_value", "item_value", "freight_value", "payment_value", "price", "freight", "line_value"):
            fmt = "#,0.00"
        if c == "retention":
            fmt = "0.00%"
        lines.append(f"\tcolumn {c}")
        lines.append(f"\t\tdataType: {dt}")
        if fmt:
            lines.append(f"\t\tformatString: {fmt}")
        if name == "dim_date" and c == "date":
            lines.append("\t\tisKey")
        if c in HIDDEN and name.startswith("fact"):
            lines.append("\t\tisHidden")
        lines.append(f"\t\tlineageTag: {tag('c', name, c)}")
        lines.append("\t\tsummarizeBy: none")
        lines.append(f"\t\tsourceColumn: {c}")
        if (name, c) in SORT_BY:
            lines.append(f"\t\tsortByColumn: {SORT_BY[(name, c)]}")
        lines.append("")
        lines.append("\t\tannotation SummarizationSetBy = Automatic")
        lines.append("")
        typed.append(f'{{"{c}", {mtype}}}')
    lines += [
        f"\tpartition {name} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        f'\t\t\t\t    Source = Parquet.Document ( File.Contents ( DataFolder & "\\{name}.parquet" ) ),',
        f"\t\t\t\t    Typed = Table.TransformColumnTypes ( Source, {{{', '.join(typed)}}} )",
        "\t\t\t\tin",
        "\t\t\t\t    Typed",
        "",
    ]
    return "\n".join(lines)


def tmdl_measures():
    lines = ["table _Measures", f"\tlineageTag: {tag('t', '_Measures')}", ""]
    for folder, name, expr, fmt, desc in MEASURES:
        if desc:
            lines.append(f"\t/// {desc}")
        lines.append(f"\tmeasure '{name}' = {expr}")
        lines.append(f"\t\tformatString: {fmt}")
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {tag('m', name)}")
        lines.append("")
    lines += ["\tcolumn Value", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {tag('c', '_Measures', 'Value')}",
              "\t\tsummarizeBy: none", "\t\tisNameInferred", "\t\tsourceColumn: [Value]", "",
              "\t\tannotation SummarizationSetBy = Automatic", "",
              "\tpartition _Measures = calculated", "\t\tmode: import", '\t\tsource = ROW ( "Value", BLANK () )', ""]
    return "\n".join(lines)


def build_model():
    sm = DASH / f"{NAME}.SemanticModel"
    d = sm / "definition"
    con = duckdb.connect()
    wjson(sm / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": tag("sm")}})
    wjson(sm / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}})
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1601\n")
    write(d / "expressions.tmdl",
          "/// Full path to the repo's data\\powerbi folder, e.g. C:\\olist-ecommerce-bi\\data\\powerbi\n"
          'expression DataFolder = "C:\\\\olist-ecommerce-bi\\\\data\\\\powerbi" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
          f"\tlineageTag: {tag('e', 'DataFolder')}\n\n\tannotation PBI_ResultType = Text\n")
    order = list(TABLES) + ["_Measures"]
    write(d / "model.tmdl",
          "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\n"
          f"annotation PBI_QueryOrder = {json.dumps(['DataFolder'] + order)}\n\n"
          + "".join(f"ref table {t}\n" for t in order))
    rel = []
    for ft, fc, tt, tc in RELS:
        rel.append(f"relationship {tag('r', ft, fc, tt)}\n\tfromColumn: {ft}.{fc}\n\ttoColumn: {tt}.{tc}\n")
    write(d / "relationships.tmdl", "\n".join(rel))
    for t in TABLES:
        write(d / "tables" / f"{t}.tmdl", tmdl_table(con, t))
    write(d / "tables" / "_Measures.tmdl", tmdl_measures())


# ---------------------------------------------------------------- report

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def field(ref):
    """'Table.Column' or '[Measure]'"""
    if ref.startswith("["):
        m = ref[1:-1]
        return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": m}},
                "queryRef": f"_Measures.{m}", "nativeQueryRef": m}
    t, c = ref.split(".", 1)
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}},
            "queryRef": ref, "nativeQueryRef": c}


def container(title):
    return {
        "title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                  "fontSize": lit("11D"), "fontFamily": lit("'Segoe UI Semibold'")}}],
        "border": [{"properties": {"show": lit("true"),
                                   "color": {"solid": {"color": lit("'#E1DFDD'")}}, "radius": lit("4D")}}],
    }


class Page:
    def __init__(self, name, display, subtitle):
        self.name, self.display, self.subtitle = name, display, subtitle
        self.visuals = []
        self.drill = None

    def add(self, vtype, title, x, y, w, h, roles, sort=None, objects=None):
        n = len(self.visuals) + 1
        v = {"visualType": vtype,
             "query": {"queryState": {role: {"projections": [field(f) for f in fs]} for role, fs in roles.items()}},
             "drillFilterOtherVisuals": True,
             "visualContainerObjects": container(title)}
        if sort:
            ref, direction = sort
            v["query"]["sortDefinition"] = {"sort": [{"field": field(ref)["field"], "direction": direction}],
                                            "isDefaultSort": True}
        if objects:
            v["objects"] = objects
        self.visuals.append((f"{self.name}_v{n:02d}", x, y, w, h, v))
        return self

    def slicer(self, title, x, y, w, h, col, dropdown=True):
        obj = {"data": [{"properties": {"mode": lit("'Dropdown'" if dropdown else "'Basic'")}}]}
        return self.add("slicer", title, x, y, w, h, {"Values": [col]}, objects=obj)

    def cards(self, measures, y=80, x0=20, w=300, h=110, gap=14):
        for i, m in enumerate(measures):
            self.add("card", m, x0 + i * (w + gap), y, w, h, {"Values": [f"[{m}]"]})
        return self


SLICER_ROW = 80
CARD_ROW = 170


def standard_slicers(p, extra=None):
    p.slicer("Year", 20, SLICER_ROW, 220, 70, "dim_date.year")
    p.slicer("Month", 254, SLICER_ROW, 220, 70, "dim_date.month_name")
    p.slicer("Region", 488, SLICER_ROW, 220, 70, "dim_state.region")
    p.slicer("Customer state", 722, SLICER_ROW, 220, 70, "dim_state.state")
    for i, (t, c) in enumerate(extra or []):
        p.slicer(t, 956 + i * 234, SLICER_ROW, 220, 70, c)


def pages():
    out = []

    p = Page("p01_overview", "Overview", "Olist marketplace, Brazil · Sep 2016 – Oct 2018 · valid orders, BRL")
    standard_slicers(p, [("Payment type", "fact_orders.payment_type")])
    p.cards(["Revenue", "Orders", "Customers", "AOV", "Avg Review", "Late Delivery %"], y=CARD_ROW, w=300)
    p.add("lineChart", "Revenue by month", 20, 300, 1180, 380, {"Category": ["dim_date.month_start"], "Y": ["[Revenue]", "[Revenue PY]"]})
    p.add("clusteredBarChart", "Revenue by region", 1214, 300, 686, 380, {"Category": ["dim_state.region"], "Y": ["[Revenue]"]}, sort=("[Revenue]", "Descending"))
    p.add("clusteredColumnChart", "Orders by weekday", 20, 694, 590, 366, {"Category": ["dim_date.weekday_name"], "Y": ["[Orders]"]}, sort=("dim_date.weekday_name", "Ascending"))
    p.add("donutChart", "Orders by payment type", 624, 694, 576, 366, {"Category": ["fact_orders.payment_type"], "Y": ["[Orders]"]})
    p.add("tableEx", "Year summary", 1214, 694, 686, 366, {"Values": ["dim_date.year", "[Revenue]", "[Revenue YoY %]", "[Orders]", "[AOV]", "[Freight %]"]})
    out.append(p)

    p = Page("p02_trends", "Trends", "Month over month, year over year and running totals")
    standard_slicers(p)
    p.cards(["Revenue YTD", "Revenue YoY %", "Revenue MoM %", "Orders YoY %"], y=CARD_ROW, w=460)
    p.add("lineChart", "Revenue vs same month last year", 20, 300, 940, 370, {"Category": ["dim_date.month_start"], "Y": ["[Revenue]", "[Revenue PY]", "[Revenue 3M Rolling]"]})
    p.add("clusteredColumnChart", "Revenue MoM %", 974, 300, 926, 370, {"Category": ["dim_date.month_start"], "Y": ["[Revenue MoM %]"]})
    p.add("lineChart", "Running total revenue", 20, 684, 940, 376, {"Category": ["dim_date.month_start"], "Y": ["[Revenue Running Total]"]})
    p.add("pivotTable", "Monthly detail", 974, 684, 926, 376, {"Rows": ["dim_date.year_month"], "Values": ["[Revenue]", "[Revenue PM]", "[Revenue MoM %]", "[Revenue YoY %]", "[Orders]", "[AOV]"]}, sort=("dim_date.year_month", "Ascending"))
    out.append(p)

    p = Page("p03_customers", "Customers", "New vs returning, RFM segments and monthly cohorts")
    standard_slicers(p, [("Customer type", "dim_customer.customer_type")])
    p.cards(["Customers", "New Customers", "Returning Customers", "Repeat Customer %", "Revenue per Customer"], y=CARD_ROW, w=364)
    p.add("clusteredBarChart", "Revenue by RFM segment", 20, 300, 620, 370, {"Category": ["dim_customer.rfm_segment"], "Y": ["[Revenue]"]}, sort=("[Revenue]", "Descending"))
    p.add("tableEx", "RFM segments", 654, 300, 620, 370, {"Values": ["dim_customer.rfm_segment", "[Customers]", "[Revenue]", "[RFM Revenue Share]", "[AOV]", "[Avg Recency Days]"]})
    p.add("lineChart", "New vs returning customers", 1288, 300, 612, 370, {"Category": ["dim_date.month_start"], "Y": ["[New Customers]", "[Returning Customers]"]})
    p.add("pivotTable", "Cohort retention (share of cohort buying in month n)", 20, 684, 1880, 376,
          {"Rows": ["mart_cohort_retention.cohort_month"], "Columns": ["mart_cohort_retention.month_n"], "Values": ["[Cohort Retention %]"]})
    out.append(p)

    p = Page("p04_products_geo", "Products & Geo", "Categories, sellers and states · right click a category to drill through")
    standard_slicers(p, [("Category", "dim_product.category"), ("Weight band", "dim_product.weight_band")])
    p.cards(["Item Revenue", "Items Sold", "Sellers", "Revenue per Seller", "Cross-state Line %"], y=CARD_ROW, w=364)
    p.add("clusteredBarChart", "Top categories by item revenue", 20, 300, 620, 760, {"Category": ["dim_product.category"], "Y": ["[Item Revenue]"]}, sort=("[Item Revenue]", "Descending"))
    p.add("clusteredBarChart", "Revenue by customer state", 654, 300, 620, 370, {"Category": ["dim_state.state_name"], "Y": ["[Revenue]"]}, sort=("[Revenue]", "Descending"))
    p.add("scatterChart", "Delivery days vs freight share by state", 1288, 300, 612, 370, {"Category": ["dim_state.state"], "X": ["[Avg Delivery Days]"], "Y": ["[Freight %]"], "Size": ["[Orders]"]})
    p.add("tableEx", "Category scorecard", 654, 684, 1246, 376, {"Values": ["dim_product.category", "[Category Rank]", "[Item Revenue]", "[Category Share]", "[Items Sold]", "[Sellers]"]}, sort=("[Item Revenue]", "Descending"))
    out.append(p)

    p = Page("p05_delivery", "Delivery & Reviews", "How delivery time and lateness move review scores")
    standard_slicers(p)
    p.cards(["Avg Delivery Days", "Late Delivery %", "Avg Review", "Low Review %", "Canceled %"], y=CARD_ROW, w=364)
    p.add("lineChart", "Late delivery % and avg review by month", 20, 300, 940, 370, {"Category": ["dim_date.month_start"], "Y": ["[Late Delivery %]", "[Avg Review]"]})
    p.add("clusteredColumnChart", "Orders by review score", 974, 300, 926, 370, {"Category": ["fact_orders.review_score"], "Y": ["[Orders]"]})
    p.add("clusteredBarChart", "Avg delivery days by state", 20, 684, 940, 376, {"Category": ["dim_state.state_name"], "Y": ["[Avg Delivery Days]"]}, sort=("[Avg Delivery Days]", "Descending"))
    p.add("tableEx", "State delivery scorecard", 974, 684, 926, 376, {"Values": ["dim_state.state_name", "dim_state.region", "[Orders]", "[Avg Delivery Days]", "[Late Delivery %]", "[Avg Review]"]})
    out.append(p)

    p = Page("p06_category_detail", "Category Detail", "Drill-through: one product category")
    p.drill = "dim_product.category"
    p.cards(["Item Revenue", "Category Share", "Category Rank", "Items Sold", "Sellers", "Avg Review"], y=80, w=300)
    p.add("lineChart", "Item revenue by month", 20, 210, 940, 420, {"Category": ["dim_date.month_start"], "Y": ["[Item Revenue]"]})
    p.add("clusteredBarChart", "Item revenue by seller state", 974, 210, 926, 420, {"Category": ["dim_seller.state"], "Y": ["[Item Revenue]"]}, sort=("[Item Revenue]", "Descending"))
    p.add("tableEx", "Top sellers in this category", 20, 644, 940, 416, {"Values": ["dim_seller.seller_key", "dim_seller.city", "dim_seller.state", "[Item Revenue]", "[Items Sold]"]}, sort=("[Item Revenue]", "Descending"))
    p.add("clusteredColumnChart", "Items by weight band", 974, 644, 926, 416, {"Category": ["dim_product.weight_band"], "Y": ["[Items Sold]"]})
    out.append(p)
    return out


VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"


def build_report():
    rp = DASH / f"{NAME}.Report"
    d = rp / "definition"
    wjson(rp / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": tag("report")}})
    wjson(rp / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    theme = "olist-light.json"
    wjson(rp / "StaticResources" / "RegisteredResources" / theme, {
        "name": "Olist Light",
        "dataColors": ["#0B5CAD", "#F28E2B", "#59A14F", "#E15759", "#76B7B2", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"],
        "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#0B5CAD",
        "good": "#59A14F", "neutral": "#EDC948", "bad": "#E15759",
        "textClasses": {"title": {"fontFace": "Segoe UI Semibold", "fontSize": 12, "color": "#252423"},
                        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": "#605E5C"},
                        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 24, "color": "#0B5CAD"}}})
    wjson(d / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})
    wjson(d / "report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.2.0/schema.json",
        "layoutOptimization": "None",
        "themeCollection": {"customTheme": {"name": theme, "reportVersionAtImport": "5.55", "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": theme, "path": theme, "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True}})
    if (d / "pages").exists():
        shutil.rmtree(d / "pages")
    ps = pages()
    wjson(d / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in ps], "activePageName": ps[0].name})
    for p in ps:
        pg = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.3.0/schema.json",
              "name": p.name, "displayName": p.display, "displayOption": "FitToPage", "height": 1080, "width": 1920}
        if p.drill:
            t, c = p.drill.split(".")
            fname = tag("drill", p.name)[:20].replace("-", "")
            pg["pageBinding"] = {"name": tag("binding", p.name)[:20].replace("-", ""), "type": "Drillthrough", "parameters": []}
            pg["filterConfig"] = {"filters": [{
                "name": fname,
                "field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}},
                "type": "Categorical", "howCreated": "Drillthrough"}]}
        wjson(d / "pages" / p.name / "page.json", pg)
        title = {"$schema": VC, "name": f"{p.name}_title",
                 "position": {"x": 20, "y": 10, "z": 0, "width": 1880, "height": 60, "tabOrder": 0},
                 "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
                     {"textRuns": [{"value": p.display, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": "#252423"}}]},
                     {"textRuns": [{"value": p.subtitle, "textStyle": {"fontSize": "10pt", "color": "#605E5C"}}]}]}}]}}}
        wjson(d / "pages" / p.name / "visuals" / f"{p.name}_title" / "visual.json", title)
        for i, (vname, x, y, w, h, v) in enumerate(p.visuals, 1):
            wjson(d / "pages" / p.name / "visuals" / vname / "visual.json", {
                "$schema": VC, "name": vname,
                "position": {"x": x, "y": y, "z": i * 1000, "width": w, "height": h, "tabOrder": i * 1000},
                "visual": v})


def main():
    build_model()
    build_report()
    wjson(DASH / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    write(DASH / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print("wrote", DASH.relative_to(ROOT))


if __name__ == "__main__":
    main()
