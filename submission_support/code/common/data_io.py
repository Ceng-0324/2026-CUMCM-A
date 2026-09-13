"""A 题只读输入接口；所有路径以项目根目录解析。"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "problemA"
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



def verify_inputs(root: Path = ROOT) -> list[dict]:
    """Compare original bytes with the provenance stored in the supplied Q1 result."""
    summary = json.loads((root / "results/q1/summary.json").read_text(encoding="utf-8"))
    files = [{"path": path, "sha256": digest}
             for path, digest in summary["provenance"]["input_sha256"].items()]
    for entry in files:
        path = root / entry["path"]
        if not path.is_file():
            raise ValueError(f"原始文件缺失：{entry['path']}")
        if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"原始文件 SHA-256 不一致：{entry['path']}")
    return files


def input_rows(name: str, root: Path = ROOT) -> list[dict]:
    sheet = read_xlsx(root / "problemA" / "附件" / name)["Sheet1"]
    if sheet["errors"]:
        raise ValueError(f"Excel 单元格错误：{name}: {sheet['errors']}")
    return [row for i, row in sheet["rows"].items() if i > 1]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")
