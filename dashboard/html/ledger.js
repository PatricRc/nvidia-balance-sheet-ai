
const page = document.querySelector("#page");
const period = document.querySelector("#period");
const announcement = document.querySelector("#announcement");
const navigation = [...document.querySelectorAll("nav a")];
const guide = document.querySelector("#guide");
const help = document.querySelector("#help");
let commonSize = false;
let statementView = "balance";

const bn = value => `${value < 0 ? "−" : ""}$${(Math.abs(value) / 1000).toFixed(2)}B`;
const change = value => `${value > 0 ? "+" : ""}${bn(value)}`;
const million = value => value.toLocaleString("en-US");
const multiple = value => `${value.toFixed(2)}×`;
const percent = value => `${(100 * value).toFixed(1)}%`;
const debt = facts => facts.debtCurrent + facts.debtNoncurrent;
const workingCapital = facts => facts.currentAssets - facts.currentLiabilities;
const currentRatio = facts => facts.currentAssets / facts.currentLiabilities;
const netCash = facts => facts.cash - debt(facts);
const netLiquid = facts => facts.cash + facts.securities - debt(facts);

function ledger(title, current, prior, rows) {
  return `<div class="table-wrap"><table aria-label="${title} in USD millions"><thead><tr><th scope="col">USD millions</th><th scope="col" class="num">${current.label}</th><th scope="col" class="num">${prior.label}</th></tr></thead><tbody>
  ${rows.map(([label, read]) => `<tr><th scope="row">${label}</th><td class="num">${million(read(current))}</td><td class="num">${million(read(prior))}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function track(label, display, segments) {
  return `<div class="bar-row"><div class="bar-label"><span>${label}</span><strong>${display}</strong></div>
  <div class="bar-track" aria-hidden="true">${segments.map(([fraction, css]) =>
    `<span class="bar ${css}" style="width:${100 * fraction}%"></span>`).join("")}</div></div>`;
}

const line = key => item => item[key];
const snapshotRows = [["Total assets", line("assets")], ["Liabilities", line("liabilities")], ["Equity", line("equity")]];
const liquidityRows = [
  ["Cash & equivalents", line("cash")], ["Current marketable securities", line("securities")],
  ["Receivables", line("receivables")], ["Inventory", line("inventory")],
  ["Other current assets", line("otherCurrent")], ["Current assets", line("currentAssets")],
  ["Current liabilities", line("currentLiabilities")], ["Working capital", workingCapital]
];
const debtRows = [
  ["Short-term debt", line("debtCurrent")], ["Long-term debt", line("debtNoncurrent")],
  ["Debt carrying amount", debt], ["Noncurrent operating leases", line("leaseNoncurrent")],
  ["Cash & equivalents", line("cash")], ["Current marketable securities", line("securities")],
  ["Cash-only net cash", netCash], ["Cash + marketable securities less debt", netLiquid]
];

function chapterContext({ current, prior, source, comparison }) {
  return `<p class="context"><strong>${current.label} · ${current.date}</strong> / vs ${prior.label} · ${prior.date} / ${comparison} / <a href="${source.url}">SEC ${source.form}</a></p>`;
}

function cover({ current, prior, source }) {
  const signals = [
    ["Total assets", bn(current.assets), `${change(current.assets - prior.assets)} vs ${prior.label}`],
    ["Working capital", bn(workingCapital(current)), "Current assets less current liabilities"],
    ["Debt carrying amount", bn(debt(current)), "Short- and long-term debt"]
  ];
  return `<header class="report-cover">
    <p class="eyebrow">DATAPAT.AI / COMPANY DOSSIER / NVDA</p>
    <h1 tabindex="-1">NVIDIA<br><em>Behind the<br> balance sheet.</em></h1>
    <p class="cover-deck">How did NVIDIA fund its expansion, and what do its filings reveal about the cash and debt behind it?</p>
    <div class="cover-actions">
      <a class="button primary" href="#snapshot">Start the analysis <span aria-hidden="true">→</span></a>
      <a class="cover-direct" href="#statements" data-open-statement="balance">Go to financial statements</a>
    </div>
  </header>
  <section class="cover-brief" aria-labelledby="cover-brief-title">
    <div class="cover-brief-heading">
      <h2 id="cover-brief-title">At a glance</h2>
      <p class="caption">${current.label} · As of ${current.date} · <a href="${source.url}">SEC ${source.form}</a></p>
    </div>
    <dl class="cover-signals">${signals.map(([label, value, detail]) =>
      `<div><dt>${label}</dt><dd>${value}</dd><dd class="caption">${detail}</dd></div>`).join("")}</dl>
  </section>
  <section class="cover-reading" aria-labelledby="cover-reading-title">
    <h2 id="cover-reading-title">How to read this report</h2>
    <ol>
      <li><a href="#snapshot">Read the position</a><p>See how liabilities and equity changed as the company grew.</p></li>
      <li><a href="#liquidity">Assess liquidity</a><p>Compare current obligations with the assets available to cover them.</p></li>
      <li><a href="#evidence">Check the evidence</a><p>Trace the calculations to the comparative statements and source filing.</p></li>
    </ol>
  </section>`;
}

function snapshot(selection) {
  const { current, prior } = selection;
  const max = Math.max(current.assets, prior.assets);
  const size = (amount, facts) => 100 * amount / (commonSize ? facts.assets : max);
  const equityChange = current.equity - prior.equity;
  const assetsChange = current.assets - prior.assets;
  return `<header class="snapshot-cover">
    <p class="eyebrow">01 / FINANCIAL POSITION</p><h1 tabindex="-1">The balance sheet expands.</h1>
    <p>Equity accounts for ${percent(equityChange / assetsChange)} of the increase in assets, measured by the change in funding balances.</p>
    <div class="cover-value"><strong>${bn(current.assets)}</strong><span>Total assets<br>${change(assetsChange)} vs ${prior.label}</span></div>
  </header>
  ${chapterContext(selection)}
  <div class="snapshot-spread">
    <section class="panel composition"><div class="card-heading"><h2>How assets were funded</h2>
      <div class="segmented" role="group" aria-label="Composition view">
        <button class="button secondary" data-mode="amount" aria-pressed="${!commonSize}">USD</button>
        <button class="button secondary" data-mode="share" aria-pressed="${commonSize}">% of assets</button>
      </div></div>
      <p class="caption">${commonSize ? "Share of each period’s total assets" : "Both periods use the same USD scale"}</p>
      <div class="funding-columns">${[prior, current].map(facts => {
        const label = value => commonSize ? percent(value / facts.assets) : bn(value);
        return `<div class="funding-column">
          <div class="funding-stack" aria-hidden="true">
            <span class="funding-equity" style="--height:${size(facts.equity, facts)}%"></span>
            <span class="funding-liabilities" style="--height:${size(facts.liabilities, facts)}%"></span>
          </div><strong>${facts.label}</strong>
          <span class="series-label"><i class="funding-equity"></i> Equity <b>${label(facts.equity)}</b></span>
          <span class="series-label"><i class="funding-liabilities"></i> Liabilities <b>${label(facts.liabilities)}</b></span>
        </div>`;
      }).join("")}</div>
    </section>
    <aside class="funding-note"><p class="eyebrow">CHANGE IN FUNDING</p><h2>Equity explains more of the increase.</h2>
      <dl><div><dt>Equity</dt><dd>${change(equityChange)}</dd></div><div><dt>Liabilities</dt><dd>${change(current.liabilities - prior.liabilities)}</dd></div>
      <div><dt>Asset increase</dt><dd>${change(assetsChange)}</dd></div></dl>
      <p class="caption">Balance changes reconcile to asset growth. This comparison describes funding composition at two dates.</p>
      <a href="#statements" data-open-statement="balance">Read the classified balance sheet →</a>
    </aside>
  </div>`;
}

function liquidity(selection) {
  const { current, prior } = selection;
  const components = liquidityRows.slice(0, 5).map(([label, read]) => [label, read(current) - read(prior)])
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const max = Math.max(...components.map(([, value]) => Math.abs(value)));
  const wcChange = workingCapital(current) - workingCapital(prior);
  const liabilityChange = current.currentLiabilities - prior.currentLiabilities;
  return `<header class="liquidity-header"><div><p class="eyebrow">02 / LIQUIDITY & WORKING CAPITAL</p>
    <h1 tabindex="-1">A wider working-capital cushion.</h1></div>
    <div class="liquidity-pull"><strong>${bn(workingCapital(current))}</strong><span>Working capital · ${change(wcChange)} vs ${prior.label}</span></div></header>
    ${chapterContext(selection)}
    <section class="coverage-strip" aria-label="Liquidity ratios">
      <div><span>Current ratio</span><strong>${multiple(currentRatio(prior))} <i>→</i> ${multiple(currentRatio(current))}</strong><small>Current assets ÷ current liabilities</small></div>
      <div><span>Cash ratio</span><strong>${multiple(prior.cash / prior.currentLiabilities)} <i>→</i> ${multiple(current.cash / current.currentLiabilities)}</strong><small>Cash and equivalents ÷ current liabilities</small></div>
    </section>
    <section class="liquidity-drivers"><h2>What drove the increase?</h2><p>Changes in current assets from ${prior.label}, ranked by magnitude. Bars share a zero line and a USD scale.</p>
      <ol>${components.map(([label, value]) => `<li><span>${label}</span>
        <div class="variance-track" aria-hidden="true"><i class="${value < 0 ? "negative" : ""}" style="--width:${50 * Math.abs(value) / max}%"></i></div><strong>${change(value)}</strong></li>`).join("")}</ol>
      <p class="note">Current assets changed by ${change(current.currentAssets - prior.currentAssets)}. Current liabilities changed by ${change(liabilityChange)}, leaving a ${change(wcChange)} change in working capital. <a href="#statements" data-open-statement="liquidity">Open the liquidity schedule →</a></p>
    </section>`;
}

function capital(selection) {
  const { current, prior } = selection;
  const positions = [netCash(current), netLiquid(current)];
  const max = Math.max(...positions.map(Math.abs));
  return `<div class="capital-feature"><header><p class="eyebrow">03 / DEBT & NET CASH</p>
    <h1 tabindex="-1">Two readings of net cash.</h1>
    <p>Including current marketable securities adds ${bn(current.securities)} to the reported cash-only net position.</p></header>
    <div class="capital-metric"><span>DEBT CARRYING AMOUNT</span><strong>${bn(debt(current))}</strong><p>${change(debt(current) - debt(prior))} vs ${prior.label}</p></div></div>
    ${chapterContext(selection)}
    <section class="capital-plot"><h2>What counts as liquidity?</h2><p>Two definitions, one zero line. Both deduct the same interest-bearing debt.</p>
      <div class="net-labels"><span>Net debt</span><span>Zero</span><span>Net cash</span></div>
      ${positions.map((value, i) => `<div class="net-row"><div><strong>${i === 0 ? "Cash only" : "Cash + marketable securities"}</strong><b>${bn(value)}</b></div>
        <div class="variance-track" aria-hidden="true"><i class="${value < 0 ? "negative" : ""}" style="--width:${50 * Math.abs(value) / max}%"></i></div></div>`).join("")}
    </section>
    <dl class="debt-breakdown">
      <div><dt>Short-term debt</dt><dd>${bn(current.debtCurrent)}</dd></div>
      <div><dt>Long-term debt</dt><dd>${bn(current.debtNoncurrent)}</dd></div>
      <div><dt>Noncurrent operating leases · separate</dt><dd>${bn(current.leaseNoncurrent)}</dd></div>
    </dl><p class="caption">Securities can carry price risk or sale restrictions. <a href="#statements" data-open-statement="debt">Open the debt schedule →</a></p>`;
}

function evidence(selection) {
  const { current, prior, source } = selection;
  const claims = [
    ["The balance sheet reconciles", `${million(current.assets)} = ${million(current.liabilities)} + ${million(current.equity)} (USD millions).`, snapshotRows],
    ["Coverage exceeds current obligations", `${million(current.currentAssets)} − ${million(current.currentLiabilities)} = ${million(workingCapital(current))} (USD millions).`, liquidityRows],
    ["The cash definition changes the result", `${million(netCash(current))} + ${million(current.securities)} = ${million(netLiquid(current))} (USD millions).`, debtRows]
  ];
  return `<header class="evidence-header"><p class="eyebrow">04 / NOTES & EVIDENCE</p>
    <h1 tabindex="-1">From claim to filing.</h1><p>Three calculations. Every input is visible and linked to the same filing.</p></header>
    ${chapterContext(selection)}
    <div class="evidence-dossier"><ol class="evidence-chain">${claims.map(([title, equation, rows], i) =>
      `<li><span class="evidence-index" aria-hidden="true">0${i + 1}</span><details>
        <summary>${title}</summary><p>${equation}</p>${ledger(title, current, prior, rows)}</details></li>`).join("")}</ol>
      <aside class="filing-stamp"><p class="eyebrow">SOURCE DOCUMENT</p><strong>${source.form}</strong><span>${current.date}</span>
      <code>${source.accession}</code><a href="${source.url}">Open SEC filing ↗</a>
      <p>No reviewed AI notes. These are editorial calculations from the selected filing.</p></aside>
    </div>`;
}

const chapters = {
  cover: { label: "Cover", render: cover },
  snapshot: { label: "Financial Position", render: snapshot, next: "liquidity" },
  liquidity: { label: "Liquidity & Working Capital", render: liquidity, next: "debt" },
  debt: { label: "Debt & Net Cash", render: capital, next: "evidence" },
  evidence: { label: "Notes & Evidence", render: evidence, next: "statements" },
  statements: { label: "Financial Statements", render: statements, next: "cover" }
};

function render({ focus = false } = {}) {
  const route = location.hash.slice(1);
  const key = Object.hasOwn(chapters, route) ? route : "cover";
  const chapter = chapters[key];
  for (const link of navigation) {
    if (link.hash === `#${key}`) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  document.title = `${chapter.label} — The Financial Ledger`;
  const chapterEnd = chapter.next
    ? `<div class="chapter-end"><span class="caption">THE FINANCIAL LEDGER · ${chapter.label}</span><a class="button primary" href="#${chapter.next}">${chapters[chapter.next].label} →</a></div>`
    : "";
  page.innerHTML = chapter.render(periods[period.value]) + chapterEnd;
  if (focus) page.querySelector("h1").focus();
}

page.addEventListener("click", event => {
  const button = event.target.closest("[data-mode], [data-statement]");
  const schedule = event.target.closest("[data-open-statement]");
  if (schedule) statementView = schedule.dataset.openStatement;
  if (!button) return;
  if (button.dataset.mode) commonSize = button.dataset.mode === "share";
  else {
    statementView = button.dataset.statement;
    announcement.textContent = `Showing ${statementViews[statementView]}.`;
  }
  const selector = button.dataset.mode ? `[data-mode="${button.dataset.mode}"]` : `[data-statement="${statementView}"]`;
  render();
  page.querySelector(selector).focus();
});
period.addEventListener("change", () => {
  render();
  announcement.textContent = `Showing ${periods[period.value].current.label}.`;
});
document.querySelector("#reset").addEventListener("click", () => {
  period.value = "q2";
  commonSize = false;
  statementView = "balance";
  render();
  announcement.textContent = "Reset to Q2 FY2027, USD composition and the balance sheet.";
});
help.addEventListener("click", () => guide.showModal());
guide.addEventListener("close", () => help.focus());
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault();
  document.querySelector("#content").focus();
});
window.addEventListener("hashchange", () => render({ focus: true }));
render();
