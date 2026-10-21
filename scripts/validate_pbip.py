"""Structural checks on the PBIP folder. No Power BI needed.

- every json file parses and has a $schema
- pages.json order matches the page folders, names match folder names
- visuals sit inside the 1920x1080 canvas and do not overlap on a page
- every table/column/measure used by a visual or filter exists in the TMDL
- relationships point at real columns, lineage tags are unique
- measure references [X] inside DAX resolve to a measure
- tmdl files use tabs for indentation
- with --schemas: validate each json against its published microsoft schema
  (needs internet and the jsonschema package)
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
errors = []


def err(msg):
    errors.append(msg)


def parse_tmdl(folder):
    cols, measures, tags = {}, {}, []
    for f in sorted((folder / "tables").glob("*.tmdl")):
        text = f.read_text()
        for i, line in enumerate(text.splitlines(), 1):
            lead = line[: len(line) - len(line.lstrip())]
            # m code inside a partition may carry spaces after the tabs
            if lead.startswith(" "):
                err(f"{f.name}:{i} space indentation")
        t = re.search(r"^table (\S+)", text, re.M).group(1)
        cols[t] = set(re.findall(r"^\tcolumn (\S+)", text, re.M))
        for m, expr in re.findall(r"^\tmeasure '([^']+)' = (.*)$", text, re.M):
            measures[m] = expr
        tags += re.findall(r"lineageTag: (\S+)", text)
    return cols, measures, tags


def walk_fields(obj, found):
    if isinstance(obj, dict):
        for kind in ("Column", "Measure"):
            if kind in obj and isinstance(obj[kind], dict) and "Property" in obj[kind]:
                ent = obj[kind]["Expression"]["SourceRef"]["Entity"]
                found.append((kind, ent, obj[kind]["Property"]))
        for v in obj.values():
            walk_fields(v, found)
    elif isinstance(obj, list):
        for v in obj:
            walk_fields(v, found)


def check_schemas(files):
    import urllib.request
    import warnings
    from jsonschema.validators import validator_for
    warnings.filterwarnings("ignore")
    cache, n = {}, 0
    for f in files:
        if f.parent.name == "RegisteredResources":
            continue
        obj = json.loads(f.read_text())
        url = obj["$schema"]
        if url not in cache:
            cache[url] = json.load(urllib.request.urlopen(url, timeout=30))
        schema = cache[url]
        for e in validator_for(schema)(schema).iter_errors(obj):
            err(f"{f.relative_to(DASH)}: schema: {e.message[:160]}")
        n += 1
    print(f"schema checked {n} files against {len(cache)} published schemas")


def main():
    pbip = list(DASH.glob("*.pbip"))
    if len(pbip) != 1:
        err("expected one .pbip")
    name = pbip[0].stem
    sm = DASH / f"{name}.SemanticModel" / "definition"
    rp = DASH / f"{name}.Report" / "definition"

    jsons = list(DASH.rglob("*.json")) + list(DASH.rglob("*.pbir")) + list(DASH.rglob("*.pbism")) + list(DASH.rglob(".platform")) + pbip
    for f in jsons:
        try:
            obj = json.loads(f.read_text())
        except Exception as e:
            err(f"{f}: bad json {e}")
            continue
        if f.parent.name != "RegisteredResources" and "$schema" not in obj:
            err(f"{f.relative_to(DASH)} has no $schema")

    cols, measures, tags = parse_tmdl(sm)
    if len(tags) != len(set(tags)):
        err("duplicate lineage tags")
    model = (sm / "model.tmdl").read_text()
    for t in re.findall(r"^ref table (\S+)", model, re.M):
        if t not in cols:
            err(f"model refs missing table {t}")
    for fc, tc in re.findall(r"fromColumn: (\S+)\n\ttoColumn: (\S+)", (sm / "relationships.tmdl").read_text()):
        for ref in (fc, tc):
            t, c = ref.split(".")
            if c not in cols.get(t, ()):
                err(f"relationship column {ref} missing")
    for m, expr in measures.items():
        for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", expr):
            if ref not in measures:
                err(f"measure {m} uses unknown [{ref}]")
        for t, c in re.findall(r"(\w+)\[([^\]]+)\]", expr):
            if c not in cols.get(t, ()):
                err(f"measure {m} uses unknown {t}[{c}]")

    order = json.loads((rp / "pages" / "pages.json").read_text())["pageOrder"]
    folders = sorted(p.name for p in (rp / "pages").iterdir() if p.is_dir())
    if sorted(order) != folders:
        err("pages.json order does not match page folders")
    nvis = 0
    for pg in order:
        page = json.loads((rp / "pages" / pg / "page.json").read_text())
        if page["name"] != pg:
            err(f"page name mismatch {pg}")
        found = []
        walk_fields(page, found)
        boxes = []
        for vf in sorted((rp / "pages" / pg / "visuals").glob("*/visual.json")):
            v = json.loads(vf.read_text())
            nvis += 1
            if v["name"] != vf.parent.name:
                err(f"visual name mismatch {vf}")
            p = v["position"]
            if p["x"] < 0 or p["y"] < 0 or p["x"] + p["width"] > page["width"] or p["y"] + p["height"] > page["height"]:
                err(f"{v['name']} outside canvas")
            for b in boxes:
                if p["x"] < b["x"] + b["width"] and b["x"] < p["x"] + p["width"] and p["y"] < b["y"] + b["height"] and b["y"] < p["y"] + p["height"]:
                    err(f"{v['name']} overlaps another visual on {pg}")
            boxes.append(p)
            walk_fields(v, found)
        for kind, ent, prop in found:
            if kind == "Measure" and prop not in measures:
                err(f"{pg}: unknown measure {prop}")
            if kind == "Column" and prop not in cols.get(ent, ()):
                err(f"{pg}: unknown column {ent}.{prop}")

    if "--schemas" in sys.argv:
        check_schemas(jsons)

    print(f"tables {len(cols)}, measures {len(measures)}, pages {len(order)}, visuals {nvis}, json files {len(jsons)}")
    if errors:
        print("\n".join("FAIL " + e for e in errors))
        sys.exit(1)
    print("pbip structure ok")


if __name__ == "__main__":
    main()
