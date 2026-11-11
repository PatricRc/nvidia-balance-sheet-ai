"""Sync DAX measures from dax/<folder>/*.dax (source of truth) into:

- dax/_all-measures.dax
- dax/*.dax headers (Table + Display folder, from dax/measure-folders.csv)
- fabric/notebooks/nb_semantic_model.ipynb      (MEASURES list, folder 01-base)
- fabric/notebooks/nb_measures_financial.ipynb  (MEASURES json, folders 02-kpi / 03-ratios / 04-analysis)

Measure order comes from MEASURE_ORDER below. Folder metadata lives in
dax/measure-folders.csv (subject + report pages). Usage:
    python scripts/build_measures.py          # write files
    python scripts/build_measures.py --check  # exit 1 if anything is out of sync
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAX = ROOT / "dax"
FOLDERS_CSV = DAX / "measure-folders.csv"
NB_BASE = ROOT / "fabric/notebooks/nb_semantic_model.ipynb"
NB_FIN = ROOT / "fabric/notebooks/nb_measures_financial.ipynb"
FOLDERS = ["01-base", "02-kpi", "03-ratios", "04-analysis"]
MEASURES_TABLE = "_Measures"
CATEGORY_LABEL = {
    "01-base": "01 Base",
    "02-kpi": "02 KPI",
    "03-ratios": "03 Ratios",
    "04-analysis": "04 Analysis",
}

MEASURE_ORDER = {
    "01-base": [
        "Total Assets", "Total Liabilities", "Total Equity", "Cash", "Long-Term Debt", "Revenue",
        "Net Income", "Operating Cash Flow", "CapEx", "Free Cash Flow", "Revenue YoY %",
        "Net Income Margin %", "Debt to Equity", "Cash Flow Is YTD",
    ],
    "02-kpi": [
        "Gross Profit", "Operating Income", "Cost of Revenue", "Current Assets", "Current Liabilities",
        "Working Capital", "Inventory", "Accounts Receivable", "Marketable Securities", "R&D Expense",
        "EPS Diluted", "Share Repurchases", "Dividends Paid", "Cash from Investing", "Cash from Financing",
        "Long-Term Debt Current", "Gross Debt", "Operating Lease Liabilities", "Net Cash",
        "Net Cash (Cash Only)", "Period Label",
    ],
    "03-ratios": [
        "Average Assets", "Average Equity", "Average Inventory", "Average Receivables", "Period Days",
        "Gross Margin %", "Operating Margin %", "Net Margin %", "R&D % of Revenue", "ROE", "ROA",
        "Current Ratio", "Quick Ratio", "Cash Ratio", "Liabilities to Assets", "Equity Multiplier",
        "Asset Turnover", "Inventory Turnover", "DIO", "DSO", "CFO to Net Income",
    ],
    "04-analysis": [
        "Revenue Standalone Quarter", "Net Income Standalone Quarter",
        "Revenue YoY Change", "Revenue QoQ Change", "Revenue QoQ %", "Net Income YoY Change",
        "Net Income YoY %", "Net Income QoQ Change", "Net Income QoQ %", "Total Assets YoY Change",
        "Total Assets YoY %", "Total Assets QoQ Change", "Total Assets QoQ %", "Equity YoY Change",
        "Equity YoY %", "Equity QoQ Change", "Equity QoQ %", "Cash YoY Change", "Cash YoY %",
        "Cash QoQ Change", "Cash QoQ %", "TTM Revenue", "TTM Net Income", "Revenue CAGR 3Y",
        "Revenue CAGR 5Y", "Common Size %", "DuPont ROE", "DuPont Check",
    ],
}

HEADER = re.compile(
    r"^// (?P<name>.+)\n// Table: (?P<table>.+)\n// Display folder: (?P<folder>.+)\n"
    r"// Format: (?P<format>.*)\n// Hidden: (?P<hidden>true|false)\n// ?(?P<description>.*)\n\n"
    r"(?P=name) =\n(?P<expr>.*?)\n*\Z",
    re.S,
)


def display_folder(category: str, subject: str, pages: list[str]) -> str:
    """Category path plus one Pages path per report page, semicolon-separated.

    Power BI puts a field in several folders when Display folder uses `;`,
    and nests with `\\` (learn.microsoft.com/power-bi/transform-model/desktop-measures).
    """
    if not subject:
        raise SystemExit(f"subject is required for category {category}")
    parts = [f"Category\\{CATEGORY_LABEL[category]}\\{subject}"]
    for page in pages:
        parts.append(f"Pages\\{page}")
    return ";".join(parts)


def load_folder_meta() -> dict[str, dict]:
    if not FOLDERS_CSV.exists():
        raise SystemExit(f"missing {FOLDERS_CSV.relative_to(ROOT)}")
    meta: dict[str, dict] = {}
    with FOLDERS_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            subject = (row.get("subject") or "").strip()
            pages_raw = (row.get("pages") or "").strip()
            if not name or not subject:
                raise SystemExit(f"{FOLDERS_CSV.name}: name and subject are required ({row})")
            pages = [p.strip() for p in pages_raw.split(";") if p.strip()]
            if name in meta:
                raise SystemExit(f"{FOLDERS_CSV.name}: duplicate measure {name}")
            meta[name] = {"subject": subject, "pages": pages}
    expected = [n for folder in FOLDERS for n in MEASURE_ORDER[folder]]
    missing = [n for n in expected if n not in meta]
    extra = [n for n in meta if n not in expected]
    if missing or extra:
        raise SystemExit(f"{FOLDERS_CSV.name}: missing {missing} / not in MEASURE_ORDER {extra}")
    return meta


def parse(path: Path) -> dict:
    m = HEADER.match(path.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"bad header/layout in {path.relative_to(ROOT)}")
    d = m.groupdict()
    return {
        "name": d["name"],
        "folder": d["folder"],
        "format": d["format"],
        "table": d["table"],
        "hidden": d["hidden"] == "true",
        "description": d["description"].strip(),
        "expr": d["expr"].rstrip(),
        "_path": path,
        "_category": path.parent.name,
    }


def load() -> dict[str, list[dict]]:
    meta = load_folder_meta()
    out: dict[str, list[dict]] = {}
    for folder in FOLDERS:
        by_name = {}
        for p in sorted((DAX / folder).glob("*.dax")):
            m = parse(p)
            info = meta[m["name"]]
            m["table"] = MEASURES_TABLE
            m["subject"] = info["subject"]
            m["pages"] = info["pages"]
            m["folder"] = display_folder(folder, info["subject"], info["pages"])
            by_name[m["name"]] = m
        order = MEASURE_ORDER[folder]
        missing = [n for n in order if n not in by_name]
        extra = [n for n in by_name if n not in order]
        if missing or extra:
            raise SystemExit(f"{folder}: missing files {missing} / not in MEASURE_ORDER {extra}")
        out[folder] = [by_name[n] for n in order]
    return out


def dax_block(m: dict) -> str:
    return (
        f"// {m['name']}\n// Table: {m['table']}\n// Display folder: {m['folder']}\n// Format: {m['format']}\n"
        f"// Hidden: {'true' if m['hidden'] else 'false'}\n// {m['description']}\n\n{m['name']} =\n{m['expr']}\n"
    )


def public(m: dict) -> dict:
    return {k: m[k] for k in ("name", "folder", "format", "table", "hidden", "description", "expr")}


def build_all(ms: dict[str, list[dict]]) -> str:
    head = (
        "// _all-measures.dax\n"
        "// NVIDIA Financials — all 84 measures, hosted on _Measures.\n"
        "// Load in Power BI Desktop / Fabric model view, or apply via the Fabric notebooks.\n"
        "// Display folders: Category\\<group>\\<subject>;Pages\\<page> (semicolon = several folders).\n"
        "// Folder metadata: dax/measure-folders.csv. GENERATED by scripts/build_measures.py — "
        "edit the per-measure .dax files and that CSV, not this file.\n\n"
    )
    base = "\n".join(dax_block(m) for m in ms["01-base"])
    rest = "\n".join(dax_block(m) for f in FOLDERS[1:] for m in ms[f])
    return head + base + "\n// ----- 02-kpi / 03-ratios / 04-analysis (nb_measures_financial) -----\n\n" + rest


class Notebook:
    def __init__(self, path: Path):
        self.path = path
        raw = path.read_text(encoding="utf-8")
        self.raw = raw
        self.ascii = raw.isascii()
        line2 = raw.splitlines()[1]
        self.indent = len(line2) - len(line2.lstrip(" "))
        self.tail = raw[len(raw.rstrip("\n")):]
        self.nb = json.loads(raw)

    def replace(self, pattern: re.Pattern, repl: str) -> None:
        hits = 0
        for c in self.nb["cells"]:
            s = "".join(c["source"])
            new, n = pattern.subn(lambda _m: repl, s)
            if n:
                # keep the cell's original storage form (one string vs list of lines)
                c["source"] = new if isinstance(c["source"], str) else new.splitlines(keepends=True)
                hits += n
        if hits != 1:
            raise SystemExit(f"{self.path.name}: expected 1 MEASURES literal, found {hits}")

    def dumps(self) -> str:
        return json.dumps(self.nb, indent=self.indent, ensure_ascii=self.ascii) + self.tail


def main() -> int:
    check = "--check" in sys.argv
    ms = load()
    outputs: dict[Path, str] = {DAX / "_all-measures.dax": build_all(ms)}
    for folder in FOLDERS:
        for m in ms[folder]:
            outputs[m["_path"]] = dax_block(m)

    nb = Notebook(NB_BASE)
    lit = "MEASURES = " + repr([public(m) for m in ms["01-base"]]) + "\n"
    nb.replace(re.compile(r"^MEASURES = \[.*?\]\n", re.M | re.S), lit)
    outputs[NB_BASE] = nb.dumps()

    nb = Notebook(NB_FIN)
    fin = [public(m) for f in FOLDERS[1:] for m in ms[f]]
    lit = "MEASURES = json.loads(r'''" + json.dumps(fin, indent=2, ensure_ascii=False) + "''')"
    if "'''" in json.dumps(fin):
        raise SystemExit("a measure contains ''' which would break the raw string")
    nb.replace(re.compile(r"MEASURES = json\.loads\(r'''.*?'''\)", re.S), lit)
    outputs[NB_FIN] = nb.dumps()

    stale = [p for p, text in outputs.items() if p.read_text(encoding="utf-8") != text]
    if check:
        for p in stale:
            print("out of sync:", p.relative_to(ROOT))
        return 1 if stale else 0
    for p in stale:
        p.write_text(outputs[p], encoding="utf-8")
        print("wrote", p.relative_to(ROOT))
    total = sum(len(v) for v in ms.values())
    print(f"{total} measures ({', '.join(f'{f}: {len(ms[f])}' for f in FOLDERS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
