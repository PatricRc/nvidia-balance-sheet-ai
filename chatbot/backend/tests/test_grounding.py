from app.grounding import check_grounding, extract_figures

NUMBERS = [206803000000.0, 0.7105, 2137000000.0, 3.905263812455306, 2026.0]


def test_verified_when_every_figure_matches_tool_output():
    answer = "Total assets were $206.8B in FY2026 (ended 2026-01-25); gross margin 71.1%; current ratio 3.91x; net cash (cash only) $2,137M."
    r = check_grounding(answer, NUMBERS)
    assert r["status"] == "verified", r
    assert r["checked"] == 4


def test_flags_invented_figures():
    r = check_grounding("Assets grew by $12.3B to $206.8B.", NUMBERS)
    assert r["status"] == "unverified" and r["ungrounded"] == ["$12.3B"]


def test_ignores_fiscal_labels_dates_and_accessions():
    figs = extract_figures("Q2 FY2027, 2026-07-26, accession 0001045810-26-000021, evidence Assets|2026-01-25|x")
    assert figs == []
