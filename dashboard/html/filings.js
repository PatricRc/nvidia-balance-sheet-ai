// SEC balance sheet figures are in USD millions. Sources and comparison scopes are in SOURCES.md.
const filings = {
  annual: {
    form: "10-K",
    accession: "0001045810-26-000021",
    url: "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm"
  },
  quarter: {
    form: "10-Q",
    accession: "0001045810-26-000075",
    url: "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm"
  }
};

const fiscal2025 = {
  label: "FY2025", date: "Jan 26, 2025", assets: 111601, liabilities: 32274, equity: 79327,
  currentAssets: 80126, currentLiabilities: 18047, cash: 8589, securities: 34621,
  receivables: 23065, inventory: 10080, otherCurrent: 3771,
  debtCurrent: 0, debtNoncurrent: 8463, leaseNoncurrent: 1519
};
const fiscal2026 = {
  label: "FY2026", date: "Jan 25, 2026", assets: 206803, liabilities: 49510, equity: 157293,
  currentAssets: 125605, currentLiabilities: 32163, cash: 10605, securities: 51951,
  receivables: 38466, inventory: 21403, otherCurrent: 3180,
  debtCurrent: 999, debtNoncurrent: 7469, leaseNoncurrent: 2572
};
const secondQuarter2027 = {
  label: "Q2 FY2027", date: "Jul 26, 2026", assets: 320272, liabilities: 91288, equity: 228984,
  currentAssets: 197412, currentLiabilities: 43019, cash: 22443, securities: 76926,
  receivables: 63059, inventory: 31575, otherCurrent: 3409,
  debtCurrent: 1000, debtNoncurrent: 32366, leaseNoncurrent: 4985
};

const periods = {
  q2: { current: secondQuarter2027, prior: fiscal2026, source: filings.quarter, comparison: "Since FY2026 close" },
  fy: { current: fiscal2026, prior: fiscal2025, source: filings.annual, comparison: "Fiscal year over year" }
};

// Additional filed balance-sheet lines, ordered Q2 FY2027, FY2026, FY2025.
const balanceDetail = {
  "Property and equipment, net": [14285, 10383, 6283],
  "Operating lease assets": [5390, 2867, 1793],
  "Goodwill": [21125, 20832, 5188],
  "Intangible assets, net": [2998, 3306, 807],
  "Deferred income tax assets": [12159, 13258, 10979],
  "Non-marketable securities": [51157, 22251, 3387],
  "Other assets": [15746, 8301, 3038],
  "Accounts payable": [15059, 9812, 6310],
  "Accrued and other current liabilities": [26960, 21352, 11737],
  "Other long-term liabilities": [10918, 7306, 4245],
  "Common stock": [24, 24, 24],
  "Additional paid-in capital": [9828, 10118, 11237],
  "Accumulated other comprehensive income (loss)": [-25, 178, 28],
  "Retained earnings": [219157, 146973, 68038]
};

// Income comparisons use matching durations. Cash flow in the 10-Q is six months YTD.
const statementPeriods = {
  q2: {
    income: {
      window: "Three months ended", dates: ["Jul 26, 2026", "Jul 27, 2025"],
      revenue: [96221, 46743], cost: [24079, 12890], gross: [72142, 33853],
      research: [7054, 4291], admin: [1354, 1122], expenses: [8408, 5413],
      operating: [63734, 28440], other: [7773, 2766], pretax: [71507, 31206],
      tax: [11819, 4784], net: [59688, 26422], eps: [2.46, 1.08]
    },
    cash: {
      window: "Six months ended · fiscal YTD", dates: ["Jul 26, 2026", "Jul 27, 2025"],
      opening: [10605, 8589], operating: [74421, 42779], investing: [-35124, -12343],
      financing: [-27459, -27386], movement: [11838, 3050], closing: [22443, 11639]
    }
  },
  fy: {
    income: {
      window: "Fiscal years ended", dates: ["Jan 25, 2026", "Jan 26, 2025"],
      revenue: [215938, 130497], cost: [62475, 32639], gross: [153463, 97858],
      research: [18497, 12914], admin: [4579, 3491], expenses: [23076, 16405],
      operating: [130387, 81453], other: [11063, 2573], pretax: [141450, 84026],
      tax: [21383, 11146], net: [120067, 72880], eps: [4.90, 2.94]
    },
    cash: {
      window: "Fiscal years ended", dates: ["Jan 25, 2026", "Jan 26, 2025"],
      opening: [8589, 7280], operating: [102718, 64089], investing: [-52228, -20421],
      financing: [-48474, -42359], movement: [2016, 1309], closing: [10605, 8589]
    }
  }
};
