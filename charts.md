# MacroUK Dashboard — Analytical Pages Specification

## 1. Purpose of this document

This document defines the product, analytical, architectural and visual requirements for completing the five analytical pages of the MacroUK Dashboard.

It is intended to provide persistent context to coding agents working inside the repository.

It is not a request to implement the entire dashboard in one uncontrolled change.

Future implementation prompts should reference this document and assign a clearly bounded piece of work, such as:

* preparing one page’s datasets;
* implementing one API router;
* building one reusable chart component;
* completing one Streamlit page;
* adding tests for one analytical module.

The agent must inspect the existing repository before making changes and preserve established project conventions unless a change is explicitly justified.

---

# 2. Product context

MacroUK Dashboard is a Python application for monitoring the UK economy and UK-sensitive financial markets.

Its purpose is to turn economic and market time series into a coherent analytical product rather than merely display raw data.

The application should help a user answer questions such as:

* Is UK economic growth strengthening or weakening?
* Are inflation pressures broadening or easing?
* Is the labour market becoming tighter or softer?
* How restrictive are monetary and credit conditions?
* Are households showing signs of financial stress?
* Are domestically exposed UK assets outperforming or underperforming?
* What are sterling, bonds and commodities signalling?

The dashboard is not intended to:

* provide investment recommendations;
* predict economic outcomes with unwarranted certainty;
* imply causality from simple correlations;
* present generated commentary as expert economic forecasting.

All analytical descriptions should be deterministic, cautious and supported by the displayed data.

---

# 3. Existing application architecture

The repository already contains an established data and application flow:

```text
External data sources
        ↓
ETL and calculated metrics
        ↓
SQLite prepared datasets
        ↓
FastAPI routers and Pydantic schemas
        ↓
Streamlit dashboard
```

The Home page has established the target standard for:

* professional visual hierarchy;
* config-driven presentation;
* clear API boundaries;
* graceful failure handling;
* responsive layouts;
* separated page, component and stylesheet responsibilities;
* deterministic analytical summaries;
* concise descriptions and observation dates.

The remaining pages should feel like parts of the same commercial product.

They must not become five unrelated Streamlit scripts with inconsistent layouts and styling.

---

# 4. Ownership and implementation approach

The project owner remains responsible for:

* product direction;
* data-source choices;
* metric definitions;
* architectural approval;
* analytical interpretation;
* review and acceptance of generated code.

AI may implement substantial portions of the remaining application, but it must work within this specification.

The agent must not silently redesign the project, add unnecessary frameworks or replace existing architecture merely because another approach is possible.

Important decisions and assumptions must be surfaced in the completion summary.

---

# 5. Scope

Five analytical pages remain:

1. Macro Pulse
2. Monetary Policy & Liquidity
3. Housing Market & Consumer Credit
4. Financial Markets & Equities
5. Currency, Commodities & Fixed Income

Each page should contain:

* a professional page header;
* a concise analytical overview;
* a small set of relevant headline indicators;
* three or four primary analytical charts;
* chart-specific explanatory copy;
* latest-observation information;
* deterministic insights where justified;
* graceful loading, missing-data and API-failure states;
* concise methodology or interpretation notes.

Not every page must use precisely the same visual arrangement, but all should use the same design language.

---

# 6. Shared page design standard

## 6.1 Recommended page structure

Each analytical page should generally follow this order:

```text
Page header
Page purpose and current-state summary

Headline KPI strip
Three or four page-specific indicators

Optional page-level insight panel
A concise deterministic interpretation

Primary analytical charts
Each in a professional chart panel

Chart-specific insight or explanatory note
Placed beneath or beside the relevant chart

Latest observations or compact supporting table

Methodology and source note
```

Avoid filling pages with decorative sections that do not improve interpretation.

## 6.2 Page header

Each page should have:

* a clear page title;
* a one-sentence description;
* an optional small category label;
* restrained styling consistent with the Home page.

The header should establish analytical purpose rather than use marketing language.

## 6.3 Headline indicators

Each page should normally contain three or four page-specific KPI cards.

KPI cards should use the existing design principles established on Home:

* consistent height;
* clear value hierarchy;
* optional delta without altering card alignment;
* concise description;
* latest observation date;
* correct direction semantics;
* no fabricated zero where comparison data is unavailable.

Do not duplicate Home’s six national headline indicators on every page. Select values that help orient the user to that page.

## 6.4 Chart panels

Every chart should sit in a structured panel containing:

* chart title;
* concise subtitle or analytical question;
* the chart itself;
* optional legend;
* latest-data or coverage metadata;
* a short interpretation note where useful.

The title should say what the chart measures.

The subtitle should explain why it matters.

Example:

```text
Economic Growth Momentum

Compare short-term quarterly growth with the broader annual trend.
```

## 6.5 Professional visual standard

Pages should feel:

* analytical;
* calm;
* modern;
* information-dense without being cramped;
* suitable for a commercial macroeconomic intelligence product.

Use:

* restrained colours;
* consistent spacing;
* clear typography;
* subtle borders;
* limited shadows;
* responsive grids;
* deliberate chart dimensions.

Avoid:

* excessive gradients;
* decorative emojis;
* oversized hero sections;
* rainbow chart palettes;
* excessive red and green;
* animations;
* glassmorphism;
* large areas of empty space without analytical purpose.

## 6.6 Responsive behaviour

Desktop layouts may use two chart columns where charts remain readable.

Charts that require width, including:

* multi-series daily charts;
* dual-axis charts;
* stacked-volume charts;
* heatmaps;

should use the full page width.

On narrower screens:

* multi-column sections should collapse cleanly;
* chart labels must remain readable;
* horizontal page overflow must be avoided;
* cards should not use rigid fixed widths.

---

# 7. Shared code organisation

The Home page established a useful separation between:

```text
pages/
components/
styles/
```

Apply the same principle to the analytical pages.

A suitable direction is:

```text
src/api/dashboard/
├── pages/
│   ├── home.py
│   ├── macro_pulse.py
│   ├── monetary_policy.py
│   ├── housing_credit.py
│   ├── financial_markets.py
│   └── global_flows.py
├── components/
│   ├── home_components.py
│   ├── shared_components.py
│   └── chart_components.py
└── styles/
    ├── home.css
    └── dashboard.css
```

This structure is illustrative rather than mandatory.

The agent should inspect current project conventions before creating files.

## 7.1 Page modules

Page files should primarily orchestrate:

* endpoint construction;
* API requests;
* validation;
* component calls;
* page-level control flow.

They should not contain hundreds of lines of CSS, chart transformation logic and repeated HTML.

## 7.2 Components

Reusable components may include:

* page header;
* section heading;
* KPI strip;
* chart panel;
* insight card;
* source note;
* empty state;
* freshness label;
* date-range selector.

Do not create a separate module for every tiny HTML fragment.

## 7.3 Styles

Shared analytical-page styling should live in an external stylesheet such as:

```text
src/api/dashboard/styles/dashboard.css
```

Do not duplicate nearly identical CSS in five page files.

Page-specific selectors are acceptable where a genuinely unique layout requires them.

## 7.4 Analytical logic

Economic interpretation and dataset transformations must not be embedded in Streamlit component functions.

Separate:

* ETL calculations;
* API response preparation;
* analytical interpretation;
* presentation rendering.

Streamlit should receive chart-ready or nearly chart-ready data.

---

# 8. API and schema standard

Each analytical page should have a clear FastAPI boundary.

The exact route structure should follow existing project conventions, but responses should be explicit and validated through Pydantic schemas.

A page-level response may conceptually resemble:

```python
{
    "page_summary": {
        "headline": str,
        "body": str
    },
    "kpis": [...],
    "charts": {
        "chart_id": {
            "metadata": {...},
            "series": [...]
        }
    },
    "insights": [...]
}
```

A single page endpoint or separate chart endpoints may both be valid.

Choose based on the existing architecture and avoid unnecessary rewrites.

Requirements:

* preserve stable and descriptive field names;
* use ISO-formatted dates;
* represent missing data as `null`, not fabricated values;
* include display metadata where it prevents hard-coding in Streamlit;
* validate responses with Pydantic;
* handle empty prepared tables cleanly;
* avoid returning raw database rows without an intentional response contract.

---

# 9. Configuration standard

Continue the existing config-driven approach.

Chart configuration should eventually define relevant metadata such as:

```yaml
chart_id:
  name: "Economic Growth Momentum"
  description: "Compare quarterly changes with the annual growth trend."
  metrics:
    - GDP_QOQ
    - GDP_YOY
  frequency: "quarterly"
  chart_type: "bar_line"
  units:
    GDP_QOQ: "%"
    GDP_YOY: "%"
```

Configuration should describe stable chart metadata.

Do not place frequently changing calculated values or entire analytical paragraphs in YAML.

Avoid using config merely to move ordinary Python logic into a different file.

---

# 10. Charting standard

Use the charting library already established in the repository. If no final choice has been established, prefer Plotly for interactive analytical charts unless the project owner approves another option.

Charts should include:

* useful hover tooltips;
* readable date axes;
* clear units;
* consistent line widths;
* restrained marker use;
* sensible legend placement;
* informative zero lines where applicable;
* clear target or reference lines where relevant;
* no unnecessary 3D effects;
* no misleading truncated axes.

## 10.1 Colours

Use consistent semantic or series colours across pages.

Examples:

* the same CPI series should not randomly change colour between charts;
* headline and core inflation should remain visually distinguishable;
* positive and negative bars may use restrained directional colours;
* Bank Rate should retain a consistent policy-series colour.

Do not rely solely on colour to distinguish important states.

## 10.2 Dual axes

Dual-axis charts may be used where the intended comparison genuinely requires different units.

When used:

* clearly label both axes;
* ensure series colours correspond to axis labels;
* avoid presenting unrelated scales as directly equivalent;
* explain the comparison in the subtitle or note.

Do not use dual axes solely to make unrelated data appear correlated.

## 10.3 Normalised charts

Use normalisation when comparing series with materially different price or index levels.

Preferred forms:

```text
Base date = 100
```

or:

```text
Cumulative return since selected start date = 0%
```

The chart must state:

* the selected baseline;
* whether values represent an index or percentage return;
* what happens when a series lacks data on the exact baseline date.

## 10.4 Mixed frequencies

Do not blindly resample every macroeconomic series to monthly frequency.

Frequency must follow the analytical question.

Examples:

* GDP remains quarterly;
* CPI and labour series remain monthly;
* market prices remain daily;
* daily market and monthly economic series may require explicit alignment, resampling or separate panels.

Never create artificial precision by forward-filling low-frequency economic data without explaining it.

## 10.5 Missing observations

Chart preparation should:

* sort by date;
* remove invalid duplicate observations intentionally;
* avoid silently converting missing values to zero;
* align series predictably;
* expose materially incomplete coverage to the user.

---

# 11. Shared analytical features

## 11.1 Date controls

Where appropriate, offer a small set of meaningful ranges:

* 1 year;
* 3 years;
* 5 years;
* 10 years;
* maximum available history.

Daily market pages may additionally support:

* 3 months;
* 6 months;
* year to date.

Do not add controls that do not affect the chart.

## 11.2 Observation freshness

Each chart or panel should communicate the latest available observation.

Different series may have different release dates.

Do not calculate one global freshness date using the maximum date across unrelated datasets and present it as though all data are equally current.

## 11.3 Deterministic insights

Insights should be generated from explicit rules, not an LLM.

Suitable statements include:

* direction of recent change;
* distance from a stated target;
* relative performance over the selected period;
* latest spread between two rates;
* whether a series is positive or negative;
* whether regional performance has diverged.

Avoid:

* unsupported causal claims;
* definitive forecasts;
* statements about historical extremes without sufficient history;
* claims that a single movement proves an economic regime.

## 11.4 Downloads

Chart data download is a useful enhancement after the core pages work.

Where added, download the transformed data being shown rather than an unrelated raw table.

This is not required for the first implementation pass unless requested.

---

# 12. Page 1 — Macro Pulse

## 12.1 Purpose

Macro Pulse answers:

> How is the UK economy performing across growth, inflation and employment?

It should provide the clearest high-level analytical view after the Home page.

## 12.2 Suggested page KPIs

Possible indicators:

* latest quarterly GDP growth;
* latest annual GDP growth;
* headline CPI inflation;
* unemployment rate;
* wage growth.

Use three or four rather than overcrowding the top of the page.

## 12.3 Chart 1 — Economic Growth Momentum

**Type:** Bar and line combination chart
**Frequency:** Quarterly

**Series:**

* `GDP_QOQ` as bars;
* `GDP_YOY` as a line.

**Purpose:**

Compare immediate quarterly momentum with the broader annual growth trend.

**Presentation requirements:**

* include a zero reference line;
* distinguish contractions from expansions;
* state both series are percentages;
* do not convert quarterly GDP into monthly observations;
* tooltip should show quarter and both values.

**Potential deterministic insight:**

* contraction;
* broadly flat activity;
* modest growth;
* stronger growth;
* annual growth strengthening or weakening.

## 12.4 Chart 2 — Inflation Pressures

**Type:** Multi-line chart
**Frequency:** Monthly

**Candidate series:**

* `CPI`;
* `CORE_CPI`;
* the repository’s available housing-related inflation measure.

The implementation agent must verify the actual metric identifier and definition before using it.

Do not substitute annual house-price growth and describe it as housing-cost inflation.

**Purpose:**

Show whether inflation is broad-based and whether underlying inflation is moving differently from headline CPI.

**Presentation requirements:**

* include a 2% reference line where appropriate;
* clearly differentiate headline and core measures;
* use percentage units;
* explain the housing-related series accurately.

**Potential deterministic insight:**

* headline CPI above, near or below target;
* core inflation above or below headline inflation;
* inflation broadening or narrowing only where the available measures support that wording.

## 12.5 Chart 3 — Labour Market Health

**Type:** Multi-line chart or coordinated chart panel
**Frequency:** Monthly

**Series:**

* `UNRATE`;
* `EMPRATE`;
* `WAGE_GROWTH`.

Because unemployment, employment and wage growth describe different concepts, consider either:

* a carefully labelled multi-axis chart;
* or two coordinated charts inside one panel.

Do not force all three onto one axis merely because their values are percentages.

**Purpose:**

Assess labour-market strength and wage pressure.

**Potential deterministic insight:**

* unemployment rising, falling or stable;
* employment rate direction;
* wage growth accelerating or slowing;
* real-wage comparison only if CPI is explicitly included and calculated correctly.

Avoid automatically describing this as a wage-price spiral.

---

# 13. Page 2 — Monetary Policy & Liquidity

## 13.1 Purpose

This page answers:

> How are Bank of England policy and financial conditions transmitting through money and business credit?

## 13.2 Suggested page KPIs

Possible indicators:

* Bank Rate;
* SONIA;
* Bank Rate–SONIA spread;
* M4 growth;
* latest corporate borrowing rate;
* lending growth to non-financial businesses.

## 13.3 Chart 1 — Policy Rate and Market Rates

**Type:** Multi-line chart
**Frequency:** Prefer daily for Bank Rate and SONIA where available

**Series:**

* `BANK_RATE_DA`;
* SONIA metric;
* a gilt yield series where available.

An ETF price must not be labelled as a yield.

If the available metric is an iShares gilt ETF price, present it separately or clearly label it as a bond-price proxy. Do not invert it and imply that it is an official yield without careful justification.

**Purpose:**

Assess how short-term market rates track official policy and how bond markets respond.

## 13.4 Chart 2 — Money Supply and Liquidity Growth

**Type:** Multi-line or restrained area chart
**Frequency:** Monthly

**Series:**

* M4 money-supply growth;
* notes and coin growth.

**Purpose:**

Track changes in broad and physical money measures.

Avoid claiming that one movement necessarily represents quantitative easing or tightening. Money growth is affected by multiple mechanisms.

## 13.5 Chart 3 — Business Credit Transmission

**Type:** Dual-axis line and bar chart
**Frequency:** Monthly

**Series:**

* borrowing cost for private non-financial corporations;
* lending growth or net lending to UK non-financial businesses.

**Purpose:**

Compare financing costs with the flow or growth of business credit.

The chart subtitle should make clear that co-movement does not by itself establish causality.

---

# 14. Page 3 — Housing Market & Consumer Credit

## 14.1 Purpose

This page answers:

> How are mortgage conditions, property activity and household borrowing evolving?

## 14.2 Suggested page KPIs

Possible indicators:

* two-year fixed mortgage rate;
* annual UK house-price growth;
* latest property transaction volume;
* net secured lending;
* net consumer credit.

## 14.3 Chart 1 — Mortgage Rates and House-Price Growth

**Type:** Dual-axis line chart
**Frequency:** Monthly

**Series:**

* two-year fixed mortgage rate;
* annual UK house-price growth.

**Purpose:**

Compare mortgage financing conditions with house-price momentum.

Use lag-aware language. Do not state that the current mortgage-rate observation directly caused the current house-price observation.

## 14.4 Chart 2 — Regional Housing Divergence

**Type:** Normalised line chart
**Frequency:** Monthly
**Baseline:** User-selected start date or clearly stated fixed baseline

**Series:**

* Greater London average property price;
* North West average property price;
* UK average property price.

**Purpose:**

Compare cumulative regional property-price performance.

All series should be rebased to 100 at the first common valid observation in the selected period.

The API or transformation layer should return:

* original values where useful;
* normalised values;
* effective baseline date.

## 14.5 Chart 3 — Buyer Composition and Transactions

**Type:** Stacked bars with total-volume line
**Frequency:** Monthly

**Candidate series:**

* cash-financed transaction volume;
* mortgage-financed transaction volume;
* total settled property transactions.

Before implementation, verify that:

```text
cash volume + mortgage volume
```

is definitionally comparable with the total transaction series.

Do not stack categories from incompatible sources or definitions without an explanatory note.

## 14.6 Chart 4 — Household Borrowing

**Type:** Multi-line chart or coordinated panels
**Frequency:** Monthly

**Series:**

* net secured lending to individuals;
* net consumer credit excluding credit cards, where available.

**Purpose:**

Compare mortgage borrowing with unsecured consumer-credit flows.

Do not conclude that increased consumer credit necessarily funds lifestyle maintenance. Present this as household borrowing composition.

---

# 15. Page 4 — Financial Markets & Equities

## 15.1 Purpose

This page answers:

> What are UK equity markets signalling about domestic activity, sectors and risk appetite?

## 15.2 Suggested page KPIs

Possible indicators:

* FTSE 100 one-month return;
* FTSE 250 one-month return;
* FTSE AIM one-month return;
* FTSE 250 relative return versus FTSE 100;
* strongest and weakest tracked sector proxy.

## 15.3 Chart 1 — UK Equity-Tier Performance

**Type:** Normalised performance line chart
**Frequency:** Daily

**Series:**

* FTSE 100;
* FTSE 250;
* FTSE AIM All-Share.

**Normalisation:**

Use either:

* cumulative percentage return from the selected start date;
* or an index rebased to 100.

**Purpose:**

Compare internationally exposed large caps with more domestically sensitive mid- and smaller-cap equities.

Use careful wording: FTSE 250 performance is informative about UK-sensitive assets but is not a direct measure of the domestic economy.

## 15.4 Chart 2 — Listed Housebuilders and Housing Data

**Type:** Normalised comparison chart or coordinated charts
**Frequency:** Mixed daily and monthly

**Series:**

* Taylor Wimpey;
* Barratt Redrow;
* UK house-price index or annual house-price growth.

Because the frequencies differ, do not simply merge all observations onto daily dates and imply equal information availability.

Preferred options:

1. resample market series to monthly and compare all series monthly; or
2. use coordinated panels with daily equities above and monthly housing data below.

**Purpose:**

Compare forward-looking listed housebuilder performance with slower-moving official housing indicators.

Describe the equities as market-based signals, not proven leading indicators unless the project later validates that relationship.

## 15.5 Chart 3 — UK Sector Proxy Performance

**Preferred type:** Normalised performance chart with optional latest-return summary
**Frequency:** Daily

**Candidate series:**

* Barclays;
* BP;
* Rio Tinto;
* GSK;
* Sage.

**Purpose:**

Compare selected listed-company proxies for financials, energy, mining, defensive healthcare and technology.

The dashboard must state that individual companies are proxies, not complete sector indices.

A heatmap may be added if it represents meaningful periods such as:

* one month;
* three months;
* year to date;
* one year.

Do not call an ordinary price chart a relative-strength-index chart. RSI is a specific technical indicator and should only be used if deliberately calculated.

---

# 16. Page 5 — Currency, Commodities & Fixed Income

## 16.1 Purpose

This page answers:

> What are sterling, UK bond assets and global commodity prices signalling about external and financial conditions?

## 16.2 Suggested page KPIs

Possible indicators:

* sterling effective exchange-rate change;
* GBP/USD one-month change;
* GBP/EUR one-month change;
* gilt ETF return;
* gold return;
* Brent crude change.

## 16.3 Chart 1 — Sterling Performance

**Type:** Normalised multi-line chart
**Frequency:** Daily where available

**Series:**

* sterling effective exchange-rate index;
* GBP/USD;
* GBP/EUR.

Raw levels are not directly comparable.

Normalise them to:

* 100 at the selected start date;
* or cumulative percentage change.

**Purpose:**

Distinguish broad sterling movement from changes against individual currencies.

## 16.4 Chart 2 — Gilts, Inflation Protection and Gold

**Type:** Normalised performance line chart
**Frequency:** Daily

**Series:**

* UK gilt ETF;
* UK index-linked gilt ETF;
* gold price in a clearly specified currency.

**Purpose:**

Compare returns across nominal sovereign bonds, inflation-linked bonds and gold.

Do not state that relative performance proves where capital is “fleeing” or that the market expects “severe inflation.” Use cautious language about relative asset performance.

## 16.5 Chart 3 — Energy Input Prices

**Type:** Normalised or raw-price line chart
**Frequency:** Daily

**Series:**

* Brent crude;
* WTI crude.

If raw prices are shown:

* use the same currency and unit;
* label the axis clearly.

If the user’s focus is relative movement, normalised performance may be more useful.

**Purpose:**

Track global oil-price pressures relevant to transport, production costs and inflation.

Do not describe oil-price movements as a direct measure of UK business margins.

---

# 17. Required data transformations

The original assumption that every series on the first three pages should be monthly is too broad.

Use the native or analytically appropriate frequency.

## 17.1 Quarterly data

Keep quarterly:

* GDP quarter-on-quarter;
* GDP year-on-year where published quarterly.

## 17.2 Monthly data

Use monthly for:

* inflation;
* labour-market indicators;
* money supply;
* business credit;
* mortgages;
* property prices;
* property transactions;
* consumer credit.

## 17.3 Daily data

Use daily for:

* equity indices;
* listed equities;
* exchange rates;
* commodity prices;
* market-traded bond funds;
* Bank Rate and SONIA where daily tracking is useful.

## 17.4 Reusable transformation helpers

Build reusable, tested functions for:

* date parsing and sorting;
* long-to-wide transformation where needed;
* first-common-date normalisation;
* cumulative percentage return;
* period return;
* monthly resampling of market data;
* latest observation extraction;
* previous observation comparison;
* aligned-series coverage checks;
* safe handling of missing baseline values.

Do not create one giant generic function with many unrelated flags.

## 17.5 Prepared datasets

Prefer purpose-built chart datasets over repeatedly transforming raw database tables inside Streamlit.

Prepared tables should be:

* deterministic;
* documented;
* reproducible;
* chart-oriented;
* regenerated through the existing pipeline.

---

# 18. Navigation

The application navigation should ultimately expose:

```text
Home
Macro Pulse
Monetary Policy & Liquidity
Housing Market & Consumer Credit
Financial Markets & Equities
Currency, Commodities & Fixed Income
```

The Home page’s “Explore the dashboard” section should eventually reflect these actual five analytical pages.

Do not leave obsolete “Coming soon” categories that no longer correspond to the final information architecture.

Navigation updates should be made only after the relevant page exists, so the application never exposes broken links.

---

# 19. Failure and empty-state handling

The Streamlit application and Uvicorn/FastAPI process may already be running during implementation.

Agents must be careful when validating changes.

Do not blindly start duplicate servers on the same ports.

Before launching a service:

* check the project’s existing run configuration;
* determine whether the relevant process is already active;
* reuse the running process where practical;
* restart only when code reload behaviour requires it;
* do not terminate unrelated Python processes.

Every page must distinguish between:

* API unavailable;
* invalid API response;
* valid response with no records;
* one chart missing while the rest of the page remains usable.

Where possible, one unavailable optional chart should not destroy the entire page.

Errors shown to users should be concise and should not expose stack traces.

Development logs may contain detailed diagnostics.

---

# 20. Testing standard

Tests should cover logic rather than CSS appearance.

Required areas include:

* normalisation from a common baseline;
* period-return calculations;
* mixed-frequency alignment;
* missing baseline handling;
* latest and previous observation calculations;
* deterministic insight thresholds;
* API response schemas;
* empty prepared datasets;
* maximum insight counts where applicable;
* chart-data ordering.

Page-specific tests should verify that required response fields are present without asserting entire generated paragraphs unnecessarily.

---

# 21. Validation standard

For each bounded implementation task, the agent should validate only the relevant layers.

Possible checks include:

```text
Run targeted unit tests
Run the relevant preparation function
Inspect the prepared SQLite table
Call the relevant FastAPI endpoint
Inspect its validated JSON
Open the Streamlit page
Check desktop and narrow layouts
Check missing-data behaviour
```

Because Streamlit and Uvicorn may already be running:

* avoid launching duplicate services;
* mention which existing service was reused;
* report when validation could not be performed safely;
* never claim visual validation unless the rendered page was actually inspected.

---

# 22. Recommended delivery sequence

Do not ask one agent to implement all five pages in a single change.

Use the following sequence.

## Phase A — Shared analytical foundation

1. Review existing chart, API and dashboard architecture.
2. Establish shared chart metadata and response conventions.
3. Create reusable normalisation and period-return helpers.
4. Create shared analytical-page components and CSS.
5. Add tests for the transformation helpers.

## Phase B — Macro Pulse reference page

1. Finalise Macro Pulse prepared datasets.
2. Finalise Macro Pulse API schemas and routers.
3. Implement the professional Macro Pulse page.
4. Add deterministic insights.
5. Validate and review.

Macro Pulse should become the reference implementation for later pages.

## Phase C — Remaining macro pages

1. Monetary Policy & Liquidity.
2. Housing Market & Consumer Credit.

Implement each as a separate bounded change.

## Phase D — Market pages

1. Financial Markets & Equities.
2. Currency, Commodities & Fixed Income.

Reuse the shared normalisation and market-chart patterns.

## Phase E — Product integration

1. Update application navigation.
2. Update Home navigation cards.
3. Review consistency across all pages.
4. Add shared methodology and source presentation.
5. Run full tests.
6. Perform final responsive and failure-state review.

---

# 23. Instructions for coding agents

When a future prompt references this document, the agent must:

1. Read this file.
2. Inspect the relevant existing files.
3. Identify the exact requested scope.
4. Preserve working behaviour outside that scope.
5. Reuse established components and utilities.
6. Avoid speculative redesign.
7. Verify metric identifiers and definitions before charting them.
8. Keep analytical claims proportional to the available evidence.
9. Add or update targeted tests.
10. Report:

* files changed;
* architecture decisions;
* assumptions;
* validation performed;
* tests passed or failed;
* anything intentionally deferred.

The agent must not:

* implement all remaining pages unless explicitly instructed;
* fabricate unavailable metrics;
* silently substitute one economic concept for another;
* hard-code current observations into Streamlit;
* place major data transformations in page rendering code;
* start duplicate application servers without checking;
* claim a visual result was checked when it was not;
* modify unrelated files merely to “clean up” the repository.

---

# 24. Definition of done for an analytical page

A page is complete for version 1 when:

* its datasets are reproducibly prepared;
* its API contract is validated;
* its charts answer the intended analytical questions;
* its layout matches the professional Home-page standard;
* its key values show appropriate units and dates;
* its commentary is deterministic and cautious;
* it handles unavailable and incomplete data gracefully;
* relevant tests pass;
* navigation works;
* the code is organised consistently with the rest of the application;
* the project owner has reviewed and accepted the result.

Sparklines, advanced forecasting, economic-release calendars and AI-generated commentary are not required for the first complete version unless separately approved.
