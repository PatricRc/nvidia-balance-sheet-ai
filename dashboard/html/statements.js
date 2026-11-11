const statementViews = {
  balance: "Balance sheet", income: "Profit & loss", cash: "Cash flow", debt: "Debt", liquidity: "Liquidity"
};

const accounting = value => value === 0 ? "—" : value < 0 ? `(${million(-value)})` : million(value);

function statementTable(title, dates, groups) {
  const bodies = groups.map(([heading, rows]) => `<tbody>
    ${heading ? `<tr class="account-heading"><th scope="rowgroup" colspan="3">${heading}</th></tr>` : ""}
    ${rows.map(([label, values, kind = "line", format = accounting]) =>
      `<tr class="account-${kind}"><th scope="row">${label}</th>${values.map(value =>
        `<td class="num">${format(value)}</td>`).join("")}</tr>`).join("")}
    </tbody>`).join("");
  return `<div class="table-wrap"><table class="accounts"><caption>${title} · USD millions unless noted</caption>
    <thead><tr><th scope="col">Line item</th>${dates.map(date => `<th scope="col" class="num">${date}</th>`).join("")}</tr></thead>${bodies}</table></div>`;
}

function balanceStatement({ current, prior }, preset) {
  const pair = key => [current[key], prior[key]];
  const detail = (name, kind) => [name, balanceDetail[name].slice(preset === "q2" ? 0 : 1, preset === "q2" ? 2 : 3), kind];
  const securities = preset === "q2"
    ? [["Marketable debt securities", [34143, 39065]], ["Marketable equity securities", [42783, 12886]]]
    : [["Marketable securities", pair("securities")]];
  return statementTable("Consolidated balance sheets", [current.date, prior.date], [
    ["Assets · Current", [
      ["Cash and cash equivalents", pair("cash")], ...securities, ["Accounts receivable, net", pair("receivables")],
      ["Inventories", pair("inventory")], ["Prepaid expenses and other current assets", pair("otherCurrent")],
      ["Total current assets", pair("currentAssets"), "subtotal"]
    ]],
    ["Assets · Noncurrent", [
      ...Object.keys(balanceDetail).slice(0, 7).map(name => detail(name)),
      ["Total assets", pair("assets"), "total"]
    ]],
    ["Liabilities · Current", [
      detail("Accounts payable"), detail("Accrued and other current liabilities"),
      ["Short-term debt", pair("debtCurrent")], ["Total current liabilities", pair("currentLiabilities"), "subtotal"]
    ]],
    ["Liabilities · Noncurrent", [
      ["Long-term debt", pair("debtNoncurrent")], ["Long-term operating lease liabilities", pair("leaseNoncurrent")],
      detail("Other long-term liabilities"), ["Total liabilities", pair("liabilities"), "subtotal"]
    ]],
    ["Shareholders’ equity", [
      ...Object.keys(balanceDetail).slice(-4).map(name => detail(name)),
      ["Total shareholders’ equity", pair("equity"), "subtotal"],
      ["Total liabilities and shareholders’ equity", [current, prior].map(f => f.liabilities + f.equity), "total"]
    ]]
  ]);
}

function profitStatement(facts) {
  return `<div class="statement-summary profit-summary">
    <div><p class="eyebrow">NET INCOME</p><strong>${bn(facts.net[0])}</strong><p>vs ${bn(facts.net[1])}</p></div>
    <div><p class="eyebrow">MARGINS · CURRENT PERIOD</p><div class="margin-ladder">${[
      ["Gross", facts.gross], ["Operating", facts.operating], ["Net", facts.net]
    ].map(([name, values]) => track(name, percent(values[0] / facts.revenue[0]), [[values[0] / facts.revenue[0], "equity"]])).join("")}</div></div>
    </div>` + statementTable("Consolidated statements of income", facts.dates, [
      ["Revenue and cost of sales", [["Revenue", facts.revenue], ["Cost of revenue", facts.cost], ["Gross profit", facts.gross, "subtotal"]]],
      ["Operating expenses", [["Research and development", facts.research], ["Sales, general and administrative", facts.admin],
        ["Total operating expenses", facts.expenses, "subtotal"], ["Operating income", facts.operating, "subtotal"]]],
      ["Non-operating items and taxes", [["Other income, net (combined)", facts.other], ["Income before income tax", facts.pretax],
        ["Income tax expense", facts.tax], ["Net income", facts.net, "total"], ["Diluted earnings per share · USD", facts.eps, "line", v => v.toFixed(2)]]]
    ]);
}

function cashBridge(facts) {
  const [start, operations, investing, financing, end] = [facts.opening, facts.operating, facts.investing, facts.financing, facts.closing].map(values => values[0]);
  let running = start;
  const steps = [["Opening", 0, start, start], ...[["Operations", operations], ["Investing", investing], ["Financing", financing]].map(([label, delta]) => {
    const before = running;
    running += delta;
    return [label, before, running, delta];
  }), ["Closing", 0, end, end]];
  const high = Math.max(...steps.flatMap(([, a, b]) => [a, b]));
  return `<figure class="cash-bridge"><figcaption>Cash bridge · ${facts.window}</figcaption>
  <ol>${steps.map(([label, a, b, delta], i) => `<li><strong>${i === 0 || i === 4 ? bn(delta) : change(delta)}</strong>
    <div class="bridge-plot" aria-hidden="true"><span class="${delta < 0 ? "outflow" : ""}" style="--bottom:${100 * Math.min(a, b) / high}%;--height:${100 * Math.abs(b - a) / high}%"></span></div><span>${label}</span></li>`).join("")}</ol></figure>`;
}

function cashStatement(facts) {
  return cashBridge(facts) + statementTable("Condensed cash flow summary", facts.dates, [
    ["Cash flows by activity", [["Net cash provided by operating activities", facts.operating],
      ["Net cash used in investing activities", facts.investing], ["Net cash used in financing activities", facts.financing],
      ["Net change in cash and cash equivalents", facts.movement, "subtotal"]]],
    ["Cash reconciliation", [["Cash and cash equivalents, beginning", facts.opening], ["Cash and cash equivalents, ending", facts.closing, "total"]]]
  ]);
}

function statements(selection) {
  const { current, prior, source } = selection;
  const preset = period.value;
  const flow = statementPeriods[preset];
  const datePair = [current.date, prior.date];
  const duration = statementView === "income" ? flow.income : statementView === "cash" ? flow.cash : null;
  const pair = fn => [current, prior].map(fn);
  let body;
  switch (statementView) {
    case "income": body = profitStatement(flow.income); break;
    case "cash": body = cashStatement(flow.cash); break;
    case "debt":
      body = statementTable("Supplemental debt schedule", datePair, [
        ["Carrying amounts", debtRows.map(([label, fn]) => [label, pair(fn), label === "Debt carrying amount" ? "total" : "line"])]
      ]);
      break;
    case "liquidity":
      body = statementTable("Supplemental liquidity schedule", datePair, [
        ["Current balances", liquidityRows.map(([label, fn]) => [label, pair(fn), label === "Working capital" ? "total" : "line"])],
        ["Coverage · multiples", [["Current ratio", pair(currentRatio), "line", multiple],
          ["Cash ratio", pair(f => f.cash / f.currentLiabilities), "line", multiple]]]
      ]);
      break;
    default: body = balanceStatement(selection, preset);
  }
  const dates = duration?.dates ?? datePair;
  return `<header class="statement-header"><p class="eyebrow">05 / FINANCIAL STATEMENTS</p><h1 tabindex="-1">The accounts.</h1>
    <p>Consolidated figures and supplemental analyst schedules, with comparative columns.</p></header>
    <div class="statement-controls" role="group" aria-label="Financial statement view">
      ${Object.entries(statementViews).map(([key, label]) => `<button type="button" class="button secondary" data-statement="${key}" aria-pressed="${statementView === key}">${label}</button>`).join("")}
    </div>
    <section class="statement-paper" aria-label="${statementViews[statementView]}">
      <div class="statement-meta"><strong>NVIDIA Corporation and Subsidiaries</strong>
      <p>${duration?.window ?? "As of"} · ${dates.join(" and ")} · <a href="${source.url}">SEC ${source.form}</a>${preset === "q2" ? " · Unaudited interim filing" : ""}</p></div>
      ${body}
      <p class="caption statement-footnote">${statementView === "balance"
        ? "Assets equal liabilities plus equity. See the filing for commitments, contingencies and notes."
        : duration ? "Comparative columns cover matching fiscal durations. See the filing for the complete statement and notes."
        : "Analyst schedule derived from filed balance-sheet values. See the filing for the underlying disclosures."} Parentheses denote negative amounts and a dash denotes a reported or calculated zero.</p>
    </section>`;
}
