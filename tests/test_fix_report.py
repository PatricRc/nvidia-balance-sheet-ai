"""Offline test of nb_build_import_model MODE="fix_report" and refresh against mocked Fabric. Run from the repo root: python3 tests/test_fix_report.py"""
import json, sys, types, copy, contextlib
import pandas as pd
sys.path.insert(0, "tests"); import pbir_samples as samples
nb = json.load(open("fabric/notebooks/nb_build_import_model.ipynb"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
helpers = next(c for c in cells if "def strip_extension" in c)

# ---------- 1. pure helpers ----------
g = {}; exec(helpers, g)
P = samples.parts()
ext = g["extension_measures"](P)
assert [m["name"] for m in ext] == ["Ledger Prior Close Date", "Ledger Prior Total Assets", "Ledger Prior Total Liabilities"]
assert ext[0]["dataType"] == "DateTime" and ext[0]["hidden"] is True and ext[1]["formatString"]
before = g["verify_parts"](P, samples.NEW); print("before:", before); assert len(before) == 3
new, removed = g["rewrite_parts"](copy.deepcopy(P), samples.NEW, "NVIDIA Financials Public")
print("refs removed:", removed)
assert removed == 7, removed   # card: 4 (proj, sort, objects expr, filter field) + From = 5; page 1; bookmark 1
assert g["verify_parts"](new, samples.NEW) == []
paths = [p["path"] for p in new]
assert "definition/reportExtensions.json" not in paths and ".platform" not in paths and len(paths) == len(P) - 2
d = {p["path"]: p for p in new}; o = {p["path"]: p for p in P}
# untouched parts are byte-identical
for k in ["StaticResources/RegisteredResources/folio.png", "definition/pages/p1/visuals/t1/visual.json",
          "definition/pages/p1/visuals/b1/visual.json", "definition/report.json", "StaticResources/RegisteredResources/theme.json"]:
    assert d[k]["payload"] == o[k]["payload"], k
cs = json.loads(g["decode"](d["definition.pbir"]))["datasetReference"]["byConnection"]["connectionString"]
print("pbir:", cs); assert samples.NEW in cs and samples.OLD not in cs and 'initial catalog="NVIDIA Financials Public"' in cs and "integrated security=ClaimsToken" in cs
card = json.loads(g["decode"](d["definition/pages/p1/visuals/a1/visual.json"]))
pr = card["visual"]["query"]["queryState"]["Data"]["projections"]
assert pr[0]["field"]["Measure"]["Expression"]["SourceRef"] == {"Entity": "_Measures"}
assert pr[0]["queryRef"] == "_Measures.Ledger Prior Total Assets"
assert card["filterConfig"]["filters"][0]["filter"]["From"][0] == {"Name": "_", "Entity": "_Measures", "Type": 0}
assert card["filterConfig"]["filters"][0]["filter"]["Where"][0]["Condition"]["Comparison"]["Left"]["Measure"]["Expression"]["SourceRef"] == {"Source": "_"}
# idempotent: rewriting the rewritten parts changes nothing
again, r2 = g["rewrite_parts"](copy.deepcopy(new), samples.NEW, "NVIDIA Financials Public"); assert r2 == 0
assert [p["payload"] for p in again] == [p["payload"] for p in new]
# pbir without connectionString is left for Rebind
assert g["repoint_pbir"]({"version": "4.0", "datasetReference": {"byConnection": {"connectionString": None}}}, "x", "y")["version"] == "4.0"
print("1. helpers: PASS")

# ---------- 2. fix_report end-to-end against mocks ----------
state = {"parts": samples.parts(), "updates": 0, "rebinds": 0,
         "measures": {f"M{i}": ("_Measures", "1") for i in range(83)} | {"Total Assets": ("_Measures", "SUM(x)")}}
class R:
    def __init__(s, j): s._j = j
    def json(s): return s._j
    def raise_for_status(s): pass
class FRC:
    def get(s, u): return R({"displayName": "NVIDIALakehouse", "properties": {"sqlEndpointProperties": {"connectionString": "x", "id": "sql"}}})
    def post(s, u, json=None, lro_wait=False):
        if u.endswith("getDefinition"): return R({"definition": {"format": "PBIR", "parts": copy.deepcopy(state["parts"])}})
        if u.endswith("updateDefinition"):
            assert json["definition"]["format"] == "PBIR"
            state["parts"] = json["definition"]["parts"]; state["updates"] += 1
        return R({})
class PRC:
    def post(s, u, json=None):
        assert u.endswith("/Rebind") and json == {"datasetId": samples.NEW}; state["rebinds"] += 1; return R({})
class M:
    def __init__(s, n, t, e): s.Name, s.Expression = n, e; s.Parent = types.SimpleNamespace(Name=t)
class TOM:
    model = types.SimpleNamespace(Tables=[types.SimpleNamespace(Name="_Measures", Columns=[types.SimpleNamespace(Name="Dummy")])])
    def all_measures(s): return [M(n, t, e) for n, (t, e) in state["measures"].items()]
    def add_measure(s, table_name, measure_name, expression, **k):
        assert k["display_folder"] == "Report\\Ledger"; state["measures"][measure_name] = (table_name, expression)
@contextlib.contextmanager
def connect(dataset, readonly, workspace):
    assert dataset == "NVIDIA Financials Public" and readonly is False   # never the Direct Lake model
    yield TOM()
fab = types.ModuleType("sempy.fabric"); fab.FabricRestClient = FRC; fab.PowerBIRestClient = PRC
fab.list_datasets = lambda workspace: pd.DataFrame({"Dataset Name": ["NVIDIA Financials", "NVIDIA Financials Public"], "Dataset Id": [samples.OLD, samples.NEW]})
fab.list_reports = lambda workspace: pd.DataFrame({"Name": ["NVIDIA-financial-report", "NVIDIA-financial-report - Public"], "Id": ["orig", "pub"]})
fab.evaluate_dax = lambda dataset, workspace, dax_string: (_ for _ in ()).throw(RuntimeError("bad DAX")) if "BROKEN" in dax_string else \
    pd.DataFrame({f"[{n}]": [1.0] for n in __import__("re").findall(r'"([^"]+)", CALCULATE', dax_string)})
def bim(dataset, workspace):
    ms = [{"name": n, "expression": e, "displayFolder": ("Report\\Ledger" if n.startswith("Ledger") else "Category\\X")}
          for n, (t, e) in state["measures"].items()] if dataset.endswith("Public") else \
         [{"name": n, "expression": e, "displayFolder": "Category\\X"} for n, (t, e) in state["measures"].items() if not n.startswith("Ledger")]
    return {"model": {"tables": [{"name": "Date"}, {"name": "_Measures", "measures": ms}], "relationships": []}}
labs = types.ModuleType("sempy_labs"); labs.get_semantic_model_bim = bim
tomm = types.ModuleType("sempy_labs.tom"); tomm.connect_semantic_model = connect
sempy = types.ModuleType("sempy"); sempy.fabric = fab
sys.modules.update({"sempy": sempy, "sempy.fabric": fab, "sempy_labs": labs, "sempy_labs.tom": tomm})
import os, tempfile
def run(mode):
    g = {}
    for c in cells:
        if c.startswith("%"): continue
        if c.strip().startswith("# Parameters"): c = f'MODE = "{mode}"'
        c = c.replace("/lakehouse/default/Files/exports", tempfile.gettempdir() + "/exports")
        exec(c, g)
    return g
EXPECTED = 84
run("fix_report")
assert state["updates"] == 1 and state["rebinds"] == 1
assert {"Ledger Prior Close Date", "Ledger Prior Total Assets", "Ledger Prior Total Liabilities"} <= set(state["measures"])
assert json.load(open(tempfile.gettempdir() + "/exports/report-ledger-measures.json"))[0]["name"] == "Ledger Prior Close Date"
print("2a. first fix_report run: PASS")
run("fix_report")                     # rerun: nothing to promote, no rewrite needed, still PASS
assert state["updates"] == 1 and state["rebinds"] == 2
print("2b. idempotent rerun: PASS")
labs.refresh_semantic_model = lambda **k: None
state["measures"]["Marketable Securities"] = state["measures"].pop("M0"); state["measures"]["Net Cash"] = state["measures"].pop("M1")
_ev = fab.evaluate_dax
fab.evaluate_dax = lambda dataset, workspace, dax_string: _ev(dataset, workspace, dax_string).assign(
    **{c: [51_951_000_000.0 if "Marketable" in c else 54_088_000_000.0] for c in ["[Marketable Securities]", "[Net Cash]"] if c[1:-1] in dax_string})
out = run("refresh")
assert len(out["promoted"]) == 3 and len(out["d_m"]) == 84
print("2e. refresh mode with promoted measures (84 shared compared, 3 promoted evaluated): PASS")
fab.evaluate_dax = _ev

# clash: model already has a different measure with a report measure's name -> nothing saved, report untouched
state.update(parts=samples.parts(), updates=0)
state["measures"] = {k: v for k, v in state["measures"].items() if not k.startswith("Ledger")} | {"Ledger Prior Total Assets": ("_Measures", "42")}
n_before = len(state["measures"])
try:
    run("fix_report"); raise SystemExit("clash not detected")
except AssertionError as ex:
    print("clash message:", str(ex)[:120])
assert state["updates"] == 0 and len(state["measures"]) == n_before
print("2c. clash stops before any change: PASS")

# broken promoted measure -> FAIL
state.update(parts=samples.parts(), updates=0)
state["measures"] = {k: v for k, v in state["measures"].items() if not k.startswith("Ledger")}
P2 = samples.parts(); e = json.loads(g["decode"](P2[2])); e["entities"][0]["measures"][2]["name"] = "Ledger BROKEN"
P2[2] = samples.enc("definition/reportExtensions.json", e)
for p in P2:
    if p["path"].endswith("a1/visual.json"):
        p["payload"] = samples.enc("x", json.loads(g["decode"](p)))["payload"]
state["parts"] = P2
try:
    run("fix_report"); raise SystemExit("broken measure not detected")
except AssertionError as ex:
    print("eval failure message:", str(ex)[:120])
print("2d. erroring promoted measure -> FAIL: PASS")
