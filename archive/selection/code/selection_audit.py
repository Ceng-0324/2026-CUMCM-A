"""Read-only audit of the three problem packages; only writes derived reports.

Run from any directory: python3 code/selection_audit.py
Requires Python's standard library and Poppler's pdftotext.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import posixpath
import statistics
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_number(ref):
    n = 0
    for char in ref:
        if not char.isalpha():
            break
        n = n * 26 + ord(char.upper()) - 64
    return n


def read_xlsx(path):
    sheets = {}
    with ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(t.text or "" for t in x.findall(".//s:t", NS))
                       for x in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        relations = {r.attrib["Id"]: r.attrib["Target"]
                     for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        for sh in workbook.findall("s:sheets/s:sheet", NS):
            target = relations[sh.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            tree = ET.fromstring(z.read(target))
            rows, formula_count, errors = {}, 0, []
            for row in tree.findall("s:sheetData/s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    v = cell.find("s:v", NS)
                    value = v.text if v is not None else None
                    typ = cell.attrib.get("t")
                    if typ == "s":
                        value = strings[int(value)] if value is not None else None
                    elif typ == "inlineStr":
                        value = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
                    elif typ == "e":
                        errors.append([cell.attrib["r"], value])
                    elif value is not None and typ not in ("str", "b"):
                        value = float(value)
                    formula_count += cell.find("s:f", NS) is not None
                    if value is not None:
                        cells[col_number(cell.attrib["r"])] = value
                rows[int(row.attrib["r"])] = cells
            dimension = tree.find("s:dimension", NS)
            sheets[sh.attrib["name"]] = {
                "dimension": dimension.attrib["ref"] if dimension is not None else None,
                "rows": rows,
                "merges": [x.attrib["ref"] for x in tree.findall("s:mergeCells/s:mergeCell", NS)],
                "formula_count": formula_count,
                "errors": errors,
            }
    return sheets


def stats(values):
    nums = [x for x in values if isinstance(x, (int, float))]
    return {"n": len(nums), "min": min(nums) if nums else None,
            "max": max(nums) if nums else None,
            "mean": statistics.fmean(nums) if nums else None,
            "negative": sum(x < 0 for x in nums), "zero": nums.count(0)}


def matrix(sheet, first_col=2, last_col=145):
    return [[sheet["rows"][i].get(j) for j in range(first_col, last_col + 1)]
            for i in sorted(sheet["rows"]) if i > 1]


def excel_date(x):
    return (datetime(1899, 12, 30) + timedelta(days=x)).date().isoformat()


def main():
    sources = ROOT / "reports/sources"
    out = ROOT / "results/selection"
    sources.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    manifest, workbooks, summary = [], {}, {}
    for p in sorted(ROOT.glob("*题/**/*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT))
        manifest.append({"path": rel, "bytes": p.stat().st_size,
                         "sha256": sha256(p.read_bytes()).hexdigest()})
        if p.suffix == ".pdf":
            subprocess.run(["pdftotext", "-layout", str(p), str(sources / (p.stem + ".txt"))], check=True)
        elif p.suffix == ".docx":
            with ZipFile(p) as z:
                tree = ET.fromstring(z.read("word/document.xml"))
                body = next(x for x in tree if x.tag.endswith("}body"))
                lines = []
                for elem in body:
                    if elem.tag.endswith("}tbl"):
                        for row in elem:
                            if row.tag.endswith("}tr"):
                                lines.append(" | ".join("".join(t.text or "" for t in cell.iter()
                                                                if t.tag.endswith("}t"))
                                                        for cell in row if cell.tag.endswith("}tc")))
                    else:
                        lines.append("".join(t.text or "" for t in elem.iter() if t.tag.endswith("}t")))
                (sources / ("B题_" + p.stem + ".txt")).write_text("\n".join(lines), encoding="utf-8")
        elif p.suffix == ".xlsx":
            workbooks[rel] = read_xlsx(p)
            summary[rel] = {}
            for name, sh in workbooks[rel].items():
                rows = sh["rows"]
                summary[rel][name] = {k: v for k, v in sh.items() if k != "rows"}
                summary[rel][name].update({
                    "xml_rows": len(rows),
                    "nonempty_cells": sum(len(r) for r in rows.values()),
                    "first_rows": dict(list(rows.items())[:3]),
                    "last_rows": dict(list(rows.items())[-2:]),
                })
    details = {}
    for p in ["A题/附件/附件1.xlsx", "A题/附件/附件2.xlsx", "C题/附件/附件1.xlsx"]:
        details[p] = {}
        for name, sh in workbooks[p].items():
            cols = sorted({c for r in sh["rows"].values() for c in r})
            details[p][name] = {str(c): stats([r.get(c) for i, r in sh["rows"].items() if i > 1])
                               for c in cols}
    for p in ["C题/附件/附件2.xlsx", "C题/附件/附件4.xlsx"]:
        details[p] = {}
        for name, sh in workbooks[p].items():
            data = matrix(sh)
            dates = [r.get(1) for i, r in sh["rows"].items() if i > 1]
            vals = [x for r in data for x in r]
            details[p][name] = {
                "shape": [len(data), len(data[0])], "stats": stats(vals),
                "missing": vals.count(None), "date_start": excel_date(dates[0]),
                "date_end": excel_date(dates[-1]), "duplicate_dates": len(dates)-len(set(dates)),
                "date_gaps": sum(b-a != 1 for a,b in zip(dates, dates[1:])),
                "duplicate_profiles": len(data)-len(set(tuple(r) for r in data)),
                "headers": sh["rows"][1],
            }
    forecast = workbooks["C题/附件/附件3.xlsx"]["Sheet1"]["rows"]
    forecasts = []
    day = None
    for i, row in forecast.items():
        if i == 1:
            continue
        if row.get(1):
            day = datetime.strptime(row[1], "%Y-%m-%d")
        hour = int(row[2].split(":")[0])
        forecasts.append((day + timedelta(hours=hour), [row.get(c) for c in range(3,27)]))
    actual = workbooks["C题/附件/附件2.xlsx"]["光伏发电实际功率"]["rows"]
    actual_lookup = {}
    for i, row in actual.items():
        if i == 1:
            continue
        dt = datetime(1899,12,30) + timedelta(days=row[1])
        for j in range(2,146):
            actual_lookup[dt + timedelta(minutes=10*(j-1))] = row[j]
    metric = {}
    for release in (0,6,12,18):
        for group, horizons in [("all",range(1,25)), ("next6",range(1,7))]:
            pairs = [(values[h-1], actual_lookup[dt+timedelta(hours=h)])
                     for dt,values in forecasts if dt.hour == release
                     for h in horizons if dt+timedelta(hours=h) in actual_lookup]
            daylight = [(f,a) for f,a in pairs if a > 100]
            metric[f"{release:02d}_{group}"] = {
                "n":len(pairs), "mae":statistics.fmean(abs(f-a) for f,a in pairs),
                "rmse":statistics.fmean((f-a)**2 for f,a in pairs)**0.5,
                "bias":statistics.fmean(f-a for f,a in pairs),
                "daylight_n":len(daylight),
                "daylight_mae":statistics.fmean(abs(f-a) for f,a in daylight) if daylight else None,
            }
    fvals = [v for _, row in forecasts for v in row]
    details["C题/附件/附件3.xlsx"] = {
        "shape": [len(forecasts),24], "missing_values": fvals.count(None),
        "blank_date_cells": sum(not row.get(1) for i,row in forecast.items() if i>1),
        "release_counts": dict(Counter(dt.hour for dt,_ in forecasts)),
        "duplicate_release_timestamps":len(forecasts)-len(set(dt for dt,_ in forecasts)),
        "stats":stats(fvals), "forecast_error_descriptive_only":metric,
    }
    for name, data in [("manifest",manifest), ("workbook_audit",summary), ("data_checks",details)]:
        (out / (name+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source_files":len(manifest),"workbooks":len(workbooks),
                      "worksheets":sum(len(w) for w in workbooks.values()),
                      "written_to":str(out)},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
