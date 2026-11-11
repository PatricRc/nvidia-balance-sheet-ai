"""Realistic PBIR v4 parts for the public report (shapes from the Fabric PBIR JSON schemas)."""
import base64, json
OLD, NEW = "28fb4dc4-d49a-4d2f-b561-85bd3a3a3a43", "c7c8841c-142d-4848-8cd2-7fb1a6569f93"
def enc(path, obj):
    data = obj if isinstance(obj, bytes) else json.dumps(obj, indent=2).encode()
    return {"path": path, "payload": base64.b64encode(data).decode(), "payloadType": "InlineBase64"}
def mref(entity, prop, ext):
    sr = {"Entity": entity}
    if ext: sr = {"Schema": "extension", "Entity": entity}
    return {"Measure": {"Expression": {"SourceRef": sr}, "Property": prop}}
pbir = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byConnection": {"connectionString":
        f'Data Source="powerbi://api.powerbi.com/v1.0/myorg/NVIDIA-BalanceSheet-AI";initial catalog="NVIDIA Financials";integrated security=ClaimsToken;semanticmodelid={OLD}'}}}
ext = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
       "name": "extension", "entities": [{"name": "_Measures", "measures": [
  {"name": "Ledger Prior Close Date", "dataType": "DateTime", "hidden": True, "formatString": "mmm d, yyyy",
   "expression": "CALCULATE(MAX('Balance Sheet'[period_end]), 'Balance Sheet'[period_end] < MAX('Date'[date]))",
   "references": {"unrecognizedReferences": False}},
  {"name": "Ledger Prior Total Assets", "dataType": "Double", "formatString": "\\$#,0,,\"M\"",
   "expression": "VAR d = [Ledger Prior Close Date] RETURN CALCULATE([Total Assets], 'Date'[date] = d)",
   "references": {"measures": [{"entity": "_Measures", "name": "Total Assets"},
                               {"schema": "extension", "entity": "_Measures", "name": "Ledger Prior Close Date"}]}},
  {"name": "Ledger Prior Total Liabilities", "dataType": "Double", "formatString": "\\$#,0,,\"M\"",
   "expression": "VAR d = [Ledger Prior Close Date] RETURN CALCULATE([Total Liabilities], 'Date'[date] = d)"}]}]}
card = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
  "name": "a1", "position": {"x": 0, "y": 0, "z": 0, "width": 200, "height": 100},
  "visual": {"visualType": "cardVisual",
    "query": {"queryState": {"Data": {"projections": [
        {"field": mref("_Measures", "Ledger Prior Total Assets", True), "queryRef": "_Measures.Ledger Prior Total Assets", "nativeQueryRef": "Ledger Prior Total Assets"},
        {"field": mref("_Measures", "Total Assets", False), "queryRef": "_Measures.Total Assets", "nativeQueryRef": "Total Assets"}]}},
      "sortDefinition": {"sort": [{"field": mref("_Measures", "Ledger Prior Total Assets", True), "direction": "Descending"}]}},
    "objects": {"labels": [{"properties": {"color": {"solid": {"color": {"expr": mref("_Measures", "Ledger Prior Total Liabilities", True)}}}}}]}},
  "filterConfig": {"filters": [{"name": "f1", "field": mref("_Measures", "Ledger Prior Total Assets", True), "type": "Advanced",
    "filter": {"Version": 2, "From": [{"Name": "_", "Entity": "_Measures", "Schema": "extension", "Type": 0}],
               "Where": [{"Condition": {"Comparison": {"ComparisonKind": 1,
                 "Left": {"Measure": {"Expression": {"SourceRef": {"Source": "_"}}, "Property": "Ledger Prior Total Assets"}},
                 "Right": {"Literal": {"Value": "0D"}}}}}]}}]}}
textbox = {"$schema": card["$schema"], "name": "t1", "position": card["position"],
  "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": "Extension of credit (text, not a ref)"}]}]}}]}}}
bar = {"$schema": card["$schema"], "name": "b1", "position": card["position"],
  "visual": {"visualType": "clusteredBarChart", "query": {"queryState": {
     "Category": {"projections": [{"field": {"Column": {"Expression": {"SourceRef": {"Entity": "Date"}}, "Property": "fiscal_year"}}, "queryRef": "Date.fiscal_year"}]},
     "Y": {"projections": [{"field": mref("_Measures", "Revenue", False), "queryRef": "_Measures.Revenue"}]}}}}}
page = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json", "name": "p1",
        "displayName": "Ledger", "filterConfig": {"filters": [{"name": "pf", "field": mref("_Measures", "Ledger Prior Close Date", True), "type": "Advanced"}]}}
bookmark = {"name": "bm1", "explorationState": {"sections": {"p1": {"filters": {"byExpr": [{"name": "x", "expression": mref("_Measures", "Ledger Prior Total Assets", True)}]}}}}}
def parts():
    return [enc(".platform", {"metadata": {"type": "Report", "displayName": "NVIDIA-financial-report - Public"}}),
            enc("definition.pbir", pbir), enc("definition/reportExtensions.json", ext),
            enc("definition/report.json", {"themeCollection": {"baseTheme": {"name": "CY24SU10"}}}),
            enc("definition/pages/p1/page.json", page),
            enc("definition/pages/p1/visuals/a1/visual.json", card),
            enc("definition/pages/p1/visuals/t1/visual.json", textbox),
            enc("definition/pages/p1/visuals/b1/visual.json", bar),
            enc("definition/bookmarks/bm1.bookmark.json", bookmark),
            enc("StaticResources/RegisteredResources/folio.png", b"\x89PNG\r\n\x1a\nfakebinary"),
            enc("StaticResources/RegisteredResources/theme.json", {"name": "Ledger", "dataColors": ["#496052"]})]
