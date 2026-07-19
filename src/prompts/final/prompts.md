# Prompt 5 — Build the Monetary Policy & Liquidity Data Layer

Read `charts.md` in full before making changes.

Prompts 1–4 have already established the shared analytical foundation and completed Macro Pulse. Treat Macro Pulse as the reference implementation.

This task is limited to preparing and testing the data, KPIs, deterministic summary and chart insights for the Monetary Policy & Liquidity page.

Do not implement the FastAPI endpoint or Streamlit page in this change.

## Objective

Prepare reproducible chart-oriented datasets for:

1. Policy Rate and Market Rates
2. Money Supply and Liquidity Growth
3. Business Credit Transmission
4. Monetary Policy headline KPIs
5. Deterministic page summary
6. Deterministic chart insights

## Existing metrics to verify and use

The metric manifest currently defines:

```text
BANK_RATE_DA
BANK_RATE_MO
SONIA
M4_GROWTH_MO
NOTES_COINS_GROWTH_MO
NET_LENDING_CORP_MO
CORP_OVERDRAFT_COST_MO
GILT_CORE
ETF_UK_GILT
```

`GILT_CORE` and `ETF_UK_GILT` both currently point to `IGLT.L`.

Do not treat this ETF price as a gilt yield.

Before implementation, inspect:

* the economic-series table;
* Yahoo price-column naming;
* metric naming after ETL;
* existing preparation modules;
* Macro Pulse preparation conventions;
* whether duplicate `IGLT.L` metric definitions create duplicate stored series.

Use one canonical gilt ETF identifier and document the decision.

## Chart datasets

### MP1 — Policy Rate and Market Rates

Required:

* `BANK_RATE_DA`
* `SONIA`

Optional:

* one clearly labelled UK gilt ETF price proxy

Preferred design:

* retain Bank Rate and SONIA at daily frequency;
* if including the gilt ETF, either:

  * prepare it as a separate coordinated series/panel; or
  * resample all three to month-end for a clearly labelled monthly comparison.

Do not invert the ETF price and present it as a yield.

Suggested prepared table:

```text
chart_monetary_policy_mp1
```

The dataset should retain:

* date;
* Bank Rate;
* SONIA;
* optional gilt ETF price;
* any derived Bank Rate–SONIA spread if analytically useful.

### MP2 — Money Supply and Liquidity Growth

Required:

* `M4_GROWTH_MO`
* `NOTES_COINS_GROWTH_MO`

Frequency:

* monthly.

Suggested table:

```text
chart_monetary_policy_mp2
```

Do not automatically describe changes as quantitative easing or tightening.

### MP3 — Business Credit Transmission

Required:

* `CORP_OVERDRAFT_COST_MO`
* `NET_LENDING_CORP_MO`

Frequency:

* monthly.

Suggested table:

```text
chart_monetary_policy_mp3
```

Preserve negative lending-growth values.

Do not scale one series merely to make it visually correlate with the other.

## KPIs

Prepare four page KPIs:

1. Bank Rate
2. SONIA
3. Bank Rate–SONIA spread
4. M4 growth or corporate borrowing cost

Use the existing Macro Pulse/Home KPI contract:

```text
kpi_id
metric_id
name
value
delta
description
date
main_unit
delta_unit
comparison_label
delta_direction
```

Suggested comparison logic:

* Bank Rate: previous distinct value;
* SONIA: previous observation;
* spread: latest calculated spread, compared with previous observation;
* M4 growth: previous monthly observation.

Use percentage points for rate changes and spreads.

## Deterministic summary

Create a service module following the Macro Pulse pattern.

The summary should assess:

* current policy-rate level and most recent direction;
* whether SONIA is broadly aligned with Bank Rate;
* whether money growth is strengthening or weakening;
* whether corporate credit conditions appear tighter or easier.

Use cautious language such as:

* “policy settings remain restrictive” only when supported by explicit configured thresholds;
* “overnight rates remain close to Bank Rate”;
* “money growth has strengthened from the previous observation”;
* “business borrowing costs remain elevated relative to recent observations.”

Avoid:

* predicting the next Bank of England decision;
* calling an ETF price a yield;
* claiming money-supply movement proves QE or QT;
* asserting causation between rates and lending.

The summary must tolerate one unavailable optional component.

## Chart insights

Create one deterministic insight per chart using the same structure as Macro Pulse.

### MP1

Possible content:

* latest Bank Rate;
* latest SONIA;
* latest spread;
* spread widening or narrowing.

### MP2

Possible content:

* latest M4 growth;
* whether M4 and notes/coin growth are moving in the same direction;
* mixed signals should remain neutral.

### MP3

Possible content:

* latest corporate borrowing cost;
* latest business-lending growth;
* whether lending is positive or negative;
* avoid causal claims.

## Configuration

Extend `configs/charts.yaml` with a new section:

```text
MonetaryPolicy
```

Use stable metadata:

* chart ID;
* name;
* description;
* metrics;
* optional metrics;
* frequency;
* chart type;
* units;
* roles;
* axes;
* display order.

Suggested IDs:

```text
MP1
MP2
MP3
```

Do not hard-code current values or generated commentary in YAML.

## Reuse requirements

Reuse:

* date preparation;
* coverage reporting;
* latest/previous observation helpers;
* monthly market resampling where required;
* existing database-writing conventions;
* KPI preparation patterns;
* Macro Pulse service structure.

Do not duplicate shared transformation functions.

## Tests

Add focused tests for:

* daily Bank Rate and SONIA alignment;
* Bank Rate–SONIA spread;
* monthly resampling if the gilt ETF is included;
* no ETF-as-yield naming;
* monthly liquidity series alignment;
* preservation of negative lending growth;
* KPI deltas;
* previous-distinct Bank Rate logic;
* summary with complete data;
* summary with missing optional gilt data;
* mixed signals producing neutral insight;
* coverage metadata.

## Validation

Run:

1. the targeted preparation process;
2. inspection of all prepared tables;
3. targeted tests;
4. relevant existing tests.

Confirm:

* no duplicate gilt series is used;
* Bank Rate and SONIA units are percentages;
* ETF values remain labelled as prices;
* all tables are date-sorted;
* no missing values are converted to zero.

Do not start duplicate Streamlit or Uvicorn processes.

## Final response

Report:

* exact metric IDs and stored column names used;
* canonical gilt ETF choice;
* tables created;
* KPI definitions;
* summary thresholds;
* tests and results;
* unavailable or deferred data;
* anything Prompt 6 must account for.

---

# Prompt 6 — Implement the Monetary Policy API and Professional Page

Read `charts.md` in full before making changes.

The Monetary Policy data layer from Prompt 5 should now exist.

This task completes the Monetary Policy & Liquidity page end-to-end:

* schemas;
* service/API assembly;
* router;
* Streamlit page;
* chart builders;
* tests;
* live validation.

Use Macro Pulse as the direct architectural and visual reference.

## Objective

Create a page answering:

> How are Bank of England policy and financial conditions transmitting through money and business credit?

## Architecture

Follow the current Macro Pulse structure:

```text
src/api/schemas/
src/api/services/
src/api/routers/
src/api/dashboard/pages/
src/api/dashboard/components/
tests/
```

Suggested files:

```text
src/api/schemas/monetary_policy.py
src/api/services/monetary_policy_api.py
src/api/routers/monetary_policy.py
src/api/dashboard/pages/monetary_policy.py
```

A separate analytical service module may be used if summary and insight logic is not already located appropriately.

Keep:

* the router thin;
* API assembly separate;
* Streamlit as orchestration;
* chart building in component functions;
* transformations out of Streamlit.

## API contract

Create a page-level response consistent with Macro Pulse:

```text
page
summary
kpis
charts
```

Charts must be returned in this order:

```text
MP1
MP2
MP3
```

Each chart should include:

* id;
* title;
* description;
* frequency;
* chart type;
* series metadata;
* records;
* insight;
* coverage;
* target or zero reference where relevant.

Expose series roles and axes explicitly.

## Route

Add a route consistent with the current API naming approach, for example:

```text
/api/monetary-policy/summary
```

or the repository-consistent equivalent.

Register the router in `src/api/main.py`.

Do not disturb existing Home or Macro Pulse routes.

## Page layout

Use:

1. analytical page header;
2. four KPI cards;
3. current-assessment summary;
4. Policy Rate and Market Rates;
5. Money Supply and Liquidity Growth;
6. Business Credit Transmission;
7. methodology note.

Reuse all shared components and `dashboard.css`.

## MP1 chart

Preferred presentation:

* Bank Rate and SONIA in the main panel;
* gilt ETF price, if included, in a coordinated secondary panel or clearly separate trace arrangement.

Requirements:

* Bank Rate displayed as a step-like line where appropriate;
* SONIA as a conventional line;
* Bank Rate–SONIA spread available in hover or insight;
* ETF explicitly called a price proxy;
* never label an ETF axis as yield;
* do not place percentage rates and ETF price on one unlabeled axis.

## MP2 chart

Use a two-line monthly chart:

* M4 growth;
* notes and coin growth.

Include:

* percentage axis;
* zero line;
* clear labels;
* restrained colours;
* no filled area if it obscures negative values.

## MP3 chart

Use a dual-axis chart:

* corporate borrowing cost as line;
* business-lending growth as bars.

Requirements:

* both axes labelled;
* series colours match axis titles where feasible;
* zero line for lending growth;
* negative bars preserved;
* subtitle explicitly says the chart compares financing costs with credit growth and does not prove causality.

## Page notes

The methodology note should mention:

* Bank Rate and SONIA update daily;
* money and credit series update monthly;
* the gilt series is an ETF price proxy rather than an official gilt yield;
* observation dates differ;
* analysis is descriptive.

## Error handling

Follow Macro Pulse behaviour:

* full API failure stops the page with a concise error;
* one empty chart renders an empty state while the page continues;
* missing optional ETF data does not fail MP1;
* absent summary or insight hides cleanly;
* no raw JSON.

## Tests

Add tests for:

* complete API response;
* chart order;
* correct rate and price units;
* optional ETF missing;
* MP1 trace types;
* Bank Rate step rendering;
* MP2 zero line;
* MP3 dual axes and bar/line roles;
* invalid API response;
* one empty chart;
* summary absent;
* route registration.

## Live validation

Reuse existing running services where possible.

Inspect:

* API JSON;
* page rendering;
* desktop layout;
* narrower layout;
* optional-data note;
* all hover units;
* Home and Macro Pulse still working.

Do not claim visual validation unless inspected.

## Final response

Report:

* files changed;
* endpoint;
* charts implemented;
* ETF treatment;
* tests;
* live validation;
* reusable patterns introduced;
* anything deferred.

---

# Prompt 7 — Build the Housing Market & Consumer Credit Data Layer

Read `charts.md` in full before making changes.

Use the completed Macro Pulse and Monetary Policy implementations as reference patterns.

This task is limited to data preparation, KPIs, deterministic summary, insights and tests for Housing Market & Consumer Credit.

Do not implement the API or Streamlit page yet.

## Existing metric inventory

Verify and use the actual manifest identifiers:

```text
MORTGAGE_2YR_75LTV_MO
UK_HPI_YOY_CHANGE_UK
UK_HPI_AVG_PRICE_UK
UK_HPI_AVG_PRICE_LONDON
UK_HPI_AVG_PRICE_NW
UK_HPI_VOLUME_UK
UK_HPI_CASH_SALES_VOL
UK_HPI_MORTGAGE_SALES_VOL
NET_LENDING_DWELLINGS_MO
NET_CONSUMER_CREDIT_MO
```

Important geography issue:

* `UK_HPI_VOLUME_UK` is UK-wide;
* `UK_HPI_CASH_SALES_VOL` and `UK_HPI_MORTGAGE_SALES_VOL` are England and Wales.

Do not stack the England-and-Wales components and overlay the UK total as though they share the same geography.

## Objective

Prepare four datasets:

```text
HC1 — Mortgage Rates and House-Price Growth
HC2 — Regional Housing Divergence
HC3 — Buyer Composition and Transaction Activity
HC4 — Household Borrowing
```

## HC1

Required:

* `MORTGAGE_2YR_75LTV_MO`
* `UK_HPI_YOY_CHANGE_UK`

Frequency:

* monthly.

Preserve independent release dates.

Do not forward-fill one series merely to eliminate gaps.

## HC2

Required:

* `UK_HPI_AVG_PRICE_UK`
* `UK_HPI_AVG_PRICE_LONDON`
* `UK_HPI_AVG_PRICE_NW`

Prepare:

* original GBP values;
* values rebased to 100;
* effective first common baseline date.

Use the shared first-common-date normalisation helper.

Do not hard-code 2020 as the baseline unless explicitly configured.

Default prepared data may use the earliest common valid date. The later page may optionally recalculate for selected ranges if the architecture supports it cleanly.

## HC3

Resolve the geography mismatch explicitly.

Preferred version 1:

* stack `UK_HPI_CASH_SALES_VOL` and `UK_HPI_MORTGAGE_SALES_VOL`;
* derive an England-and-Wales total as their sum;
* label the chart England and Wales;
* do not overlay `UK_HPI_VOLUME_UK` on the same composition chart.

The UK total may be:

* omitted from HC3;
* exposed as a separate KPI;
* or retained in separate supporting metadata.

Before using the derived total, verify:

* both components use compatible definitions;
* neither includes overlapping categories;
* dates align;
* sum behaves plausibly.

If definitions cannot be verified, do not stack them. Fall back to separate lines and report the limitation.

## HC4

Required:

* `NET_LENDING_DWELLINGS_MO`
* `NET_CONSUMER_CREDIT_MO`

Frequency:

* monthly.

Units:

* GBP millions.

Preserve negative flows.

## KPIs

Prepare four:

1. two-year fixed mortgage rate;
2. UK annual house-price growth;
3. latest UK transaction volume;
4. net secured lending or net consumer credit.

Suggested comparisons:

* mortgage rate: previous monthly observation;
* house-price growth: previous monthly observation;
* transaction volume: previous available month, with percentage change if appropriate;
* lending: previous monthly observation in GBP millions.

Do not use positive/negative colour semantics simplistically for transaction or credit volumes. Direction is not always inherently favourable.

## Summary

Assess:

* mortgage-rate direction;
* house-price momentum;
* transaction activity;
* household borrowing composition.

Use cautious wording:

* “mortgage rates have increased/decreased from the previous observation”;
* “annual house-price growth remains positive/negative”;
* “transaction activity is above/below its previous observation”;
* “secured lending and consumer credit are moving in the same/opposite direction.”

Avoid:

* calling the page a definitive measure of household stress;
* claiming current mortgage rates caused current house prices;
* saying consumer credit is funding lifestyle maintenance;
* predicting a housing crash.

## Insights

Create one per chart:

* HC1: mortgage rate direction and house-price growth state;
* HC2: strongest and weakest normalised regional performance;
* HC3: cash share of E&W derived total and recent direction;
* HC4: secured versus consumer-credit flow direction.

For HC2, calculate regional divergence from the common baseline.

For HC3, calculate cash share only when the denominator is positive and valid.

## Configuration

Add:

```text
HousingCredit
```

to `configs/charts.yaml`.

Suggested IDs:

```text
HC1
HC2
HC3
HC4
```

Include accurate geographic labels.

## Tests

Test:

* monthly alignment;
* regional common-baseline normalisation;
* baseline date returned;
* missing regional value;
* zero baseline rejection;
* E&W component sum;
* cash-share calculation;
* explicit non-use of UK total in the E&W stack;
* negative lending values;
* KPI deltas;
* summary with missing transactions;
* neutral direction for mixed borrowing signals;
* coverage.

## Validation

Inspect prepared tables and compare source values.

Explicitly report:

* whether the E&W transaction definitions were compatible;
* whether HC3 uses a derived total;
* whether UK total is excluded;
* effective regional baseline;
* date coverage differences.

Do not start duplicate servers.

## Final response

Report metrics, tables, geographic decisions, transformations, tests and API requirements.

---

# Prompt 8 — Implement the Housing & Credit API and Professional Page

Read `charts.md`.

The Housing data layer from Prompt 7 should now exist.

Complete the page end-to-end using the established analytical-page architecture.

## Objective

Build:

* Pydantic schemas;
* response assembly service;
* router;
* Streamlit page;
* Plotly figure builders;
* tests;
* live validation.

## API

Return:

```text
page
summary
kpis
charts
```

Chart order:

```text
HC1
HC2
HC3
HC4
```

Expose:

* original and normalised values where relevant;
* effective baseline date for HC2;
* geographic metadata for HC3;
* axes and units;
* coverage;
* insights.

Register the router in `src/api/main.py`.

## Page structure

1. Header
2. Headline indicators
3. Current assessment
4. Mortgage Rates and House-Price Growth
5. Regional Housing Divergence
6. Buyer Composition and Transaction Activity
7. Household Borrowing
8. Methodology note

## HC1 chart

Dual-axis monthly lines:

* mortgage rate, left;
* house-price growth, right.

Requirements:

* both axes labelled;
* no implication of contemporaneous causality;
* percentage formatting;
* clear latest-date metadata.

## HC2 chart

Normalised lines:

* UK;
* London;
* North West.

Requirements:

* baseline = 100;
* effective baseline date displayed;
* hover includes normalised value and original GBP price if returned;
* no misleading raw-price comparison on the main axis;
* full-width chart.

## HC3 chart

Use the data-layer decision.

If compatible E&W volumes were verified:

* stacked cash and mortgage-financed bars;
* optional derived total line;
* label all content “England and Wales.”

Do not overlay UK-wide transaction volume.

If composition compatibility was not verified:

* render separate lines or a documented empty state;
* do not force a stacked chart.

## HC4 chart

Two monthly lines or bars:

* net secured lending;
* net consumer credit excluding credit cards.

Use GBP millions.

Include a zero line.

Do not imply that higher borrowing is automatically positive or negative.

## Page methodology

State:

* mortgage, credit and HPI data update monthly;
* official housing series may be revised;
* regional and transaction geographies differ;
* HC3 uses E&W data where applicable;
* observation dates vary;
* analysis is descriptive.

## Error handling

Follow the existing page pattern.

One missing chart should not destroy the page.

A missing baseline should produce a clear HC2 empty state.

## Tests

Test:

* response schema;
* chart order;
* baseline metadata;
* E&W geography metadata;
* no UK total in E&W stack;
* HC1 dual axes;
* HC2 rebased traces;
* HC3 stacking;
* HC4 zero line;
* partial-data handling;
* invalid response;
* page import and route registration.

## Live validation

Inspect all four charts, labels, units, tooltips, narrower layout and existing pages.

## Final response

Report implementation, geography treatment, tests, visual validation and limitations.

---

# Prompt 9 — Build the Financial Markets & Equities Data Layer

Read `charts.md`.

This task prepares the data and deterministic analysis for Financial Markets & Equities.

Do not implement the API or page yet.

## Existing metrics

Verify actual stored identifiers derived from:

```text
FTSE_100
FTSE_250
FTSE_AIM
EQ_TW
EQ_BAR
EQ_BARC
EQ_BP
EQ_RIO
EQ_GSK
SGE_L
UK_HPI_INDEX_UK
UK_HPI_YOY_CHANGE_UK
```

Note that Yahoo ETL may store field-suffixed identifiers such as `_close`. Inspect actual database values before coding.

## Datasets

### FM1 — UK Equity-Tier Performance

Series:

* FTSE 100;
* FTSE 250;
* FTSE AIM.

Prepare:

* original close;
* normalised index from first common valid date;
* cumulative return;
* 21-session return;
* 63-session return;
* year-to-date return where sufficient data exists.

Use trading observations, not calendar-day offsets, unless a date-based helper is intentionally selected.

### FM2 — Listed Housebuilders and Official Housing Data

Series:

* Taylor Wimpey;
* Barratt Redrow;
* UK HPI index or annual UK house-price growth.

Because frequencies differ:

Preferred preparation:

* daily original housebuilder data;
* month-end housebuilder data;
* monthly HPI data;
* monthly aligned normalised comparison.

Do not forward-fill monthly HPI to daily dates for the main comparison.

Prepare coordinated datasets if needed:

```text
FM2_DAILY
FM2_MONTHLY
```

or an equivalent clean structure.

### FM3 — Sector Proxy Performance

Series:

* Barclays;
* BP;
* Rio Tinto;
* GSK;
* Sage.

Prepare:

* normalised performance;
* one-month return;
* three-month return;
* year-to-date return;
* latest available close.

These are company proxies, not complete sector indices.

## KPIs

Prepare four:

1. FTSE 100 one-month return;
2. FTSE 250 one-month return;
3. FTSE AIM one-month return;
4. FTSE 250 relative performance versus FTSE 100 over one month.

Optionally replace one with strongest tracked sector proxy if justified.

Use percentage returns.

## Summary

Assess:

* broad UK equity direction;
* domestic-sensitive relative performance;
* small-cap risk appetite;
* strongest and weakest tracked company proxies.

Avoid:

* saying FTSE 250 directly measures the UK economy;
* claiming share prices prove future housing changes;
* describing single-company performance as complete sector performance;
* investment advice.

## Insights

* FM1: best/worst index since baseline and latest relative return;
* FM2: relative monthly performance of housebuilders and HPI, carefully described;
* FM3: strongest and weakest proxy over selected default period.

## Configuration

Add:

```text
FinancialMarkets
```

with IDs:

```text
FM1
FM2
FM3
```

Include proxy disclaimers and mixed-frequency metadata.

## Tests

Test:

* exact stored Yahoo metric resolution;
* common-baseline normalisation;
* insufficient-history returns;
* year-to-date calculation;
* no weekend/calendar assumptions;
* monthly market resampling;
* monthly HPI alignment;
* no daily HPI forward-fill;
* strongest/weakest ranking;
* missing one company;
* KPI relative return;
* summary language.

## Validation

Inspect source coverage and prepared outputs.

Report ticker failures or missing history explicitly.

## Final response

Report actual metric IDs, prepared tables, frequencies, return definitions, tests and API requirements.

---

# Prompt 10 — Implement the Financial Markets API and Professional Page

Read `charts.md`.

Complete Financial Markets & Equities using the same page-level architecture as Macro Pulse.

## API and files

Create:

* schemas;
* API assembly service;
* router;
* Streamlit page;
* market figure builders;
* tests.

Register the router.

Return chart order:

```text
FM1
FM2
FM3
```

## Page layout

1. Header
2. Four market KPIs
3. Current assessment
4. UK Equity-Tier Performance
5. Listed Housebuilders and Housing Data
6. Sector Proxy Performance
7. Proxy and methodology note

## Optional date control

Add a restrained period selector only if it can be supported without bypassing the API architecture.

Suggested values:

```text
1Y
3Y
5Y
Max
```

For version 1, a configured default period is acceptable.

Do not implement filters that only alter labels while leaving data unchanged.

## FM1

Normalised line chart:

* FTSE 100;
* FTSE 250;
* FTSE AIM.

Display:

* baseline date;
* cumulative percentage return or index=100, clearly labelled;
* hover with original close and normalised value where available.

## FM2

Preferred coordinated panel:

* daily or monthly normalised housebuilder equities;
* monthly official HPI in a separate aligned panel.

Do not imply equal publication frequency.

A fully monthly comparison is also acceptable if cleaner.

Clearly label official housing data as monthly.

## FM3

Normalised proxy-performance chart.

Optionally include a compact period-return heatmap only if:

* return calculations already exist;
* it improves interpretation;
* it does not duplicate the line chart without value.

Label each company and represented industry.

Include a note that the companies are selected proxies.

## Tests

Test:

* API schema and ordering;
* normalised chart trace count;
* baseline metadata;
* mixed-frequency treatment;
* no daily HPI forward-fill;
* proxy labels;
* optional heatmap values;
* empty series;
* invalid API response;
* page import.

## Live validation

Check:

* long daily series performance;
* hover responsiveness;
* legends;
* narrow layout;
* proxy notes;
* existing pages.

## Final response

Report endpoint, charts, controls, tests, inspection and limitations.

---

# Prompt 11 — Build the Currency, Commodities & Fixed Income Data Layer

Read `charts.md`.

Prepare the data layer for the final analytical page.

## Existing metrics

Verify actual stored identifiers for:

```text
STERLING_ERI_MO
FX_GBP_USD
FX_GBP_EUR
USD_GBP_SPOT_MO
EUR_GBP_SPOT_MO
ETF_UK_GILT
ETF_UK_TIPS
COM_GOLD
COM_OIL_BRENT
COM_OIL_WTI
```

Important:

* `STERLING_ERI_MO` is monthly;
* Yahoo GBP/USD and GBP/EUR are daily;
* monthly BoE spot-rate alternatives also exist;
* gold is USD per ounce;
* Brent and WTI are USD per barrel;
* gilt series are ETF prices, not yields.

## Dataset decisions

### GF1 — Sterling Performance

Use a consistent frequency.

Preferred version:

* `STERLING_ERI_MO`;
* `USD_GBP_SPOT_MO`;
* `EUR_GBP_SPOT_MO`;

all monthly and normalised to 100.

Alternatively, resample daily Yahoo FX to month-end, but do not combine daily FX with monthly ERI without explicit alignment.

Verify direction:

* the BoE series names indicate USD per GBP and EUR per GBP;
* higher values therefore indicate stronger GBP against those currencies.

Document this.

### GF2 — Gilts, Inflation Protection and Gold

Series:

* `ETF_UK_GILT`;
* `ETF_UK_TIPS`;
* `COM_GOLD`.

Use daily normalised performance.

Gold remains USD-denominated unless an explicit GBP conversion is implemented.

Do not call ETF prices yields.

Do not claim outperformance proves inflation expectations.

### GF3 — Energy Input Prices

Series:

* Brent;
* WTI.

Both are USD per barrel.

Prepare:

* raw prices;
* normalised performance;
* 21-session returns;
* 63-session returns;
* latest Brent–WTI spread if useful.

## KPIs

Prepare four:

1. sterling ERI monthly change;
2. GBP/USD monthly change;
3. gilt ETF one-month return;
4. Brent one-month return.

Alternative choices are acceptable if clearly justified.

## Summary

Assess:

* broad sterling direction;
* bilateral sterling direction;
* relative gilt/index-linked/gold performance;
* oil-price direction.

Avoid:

* saying assets prove capital flight;
* saying index-linked gilt outperformance proves severe inflation;
* direct business-margin claims;
* financial advice.

## Insights

* GF1: broad and bilateral sterling alignment/divergence;
* GF2: best and weakest normalised asset over default period;
* GF3: Brent and WTI direction and spread.

## Configuration

Add:

```text
GlobalFlows
```

with:

```text
GF1
GF2
GF3
```

Include frequency, currency and proxy metadata.

## Tests

Test:

* monthly sterling alignment;
* exchange-rate direction conventions;
* normalisation;
* daily asset common baseline;
* gold USD unit;
* ETF price labels;
* oil units;
* return calculations;
* Brent–WTI spread;
* missing TIPS series;
* summary and neutral mixed signals.

## Validation

Inspect data coverage and ticker availability.

Report whether BoE monthly or resampled Yahoo FX was selected and why.

## Final response

Report metrics, frequency decisions, units, tables, tests and Prompt 12 requirements.

---

# Prompt 12 — Implement the Currency, Commodities & Fixed Income API and Page

Read `charts.md`.

Complete the Global Flows page end-to-end.

## API

Create page-level schemas and response consistent with previous pages.

Chart order:

```text
GF1
GF2
GF3
```

Register the router in `src/api/main.py`.

## Page title

```text
Currency, Commodities & Fixed Income
```

Description:

```text
Track sterling, UK bond assets and global commodity-price conditions.
```

## Layout

1. Header
2. Four KPIs
3. Current assessment
4. Sterling Performance
5. Gilts, Inflation Protection and Gold
6. Energy Input Prices
7. Currency, proxy and methodology note

## GF1

Monthly normalised lines:

* sterling ERI;
* GBP/USD;
* GBP/EUR.

Requirements:

* baseline=100;
* effective baseline date;
* clear wording that higher bilateral values mean stronger GBP;
* no raw-level comparison on the main axis.

## GF2

Daily normalised performance:

* nominal gilt ETF;
* index-linked gilt ETF;
* gold.

Requirements:

* identify ETFs as prices/returns;
* identify gold as USD-denominated;
* no yield terminology;
* no inflation-expectation certainty.

## GF3

Brent and WTI:

* raw USD/barrel chart or normalised comparison;
* preferably provide a user-readable raw-price view;
* optional secondary spread line only if clear;
* consistent units.

## Tests

Test:

* response shape and order;
* baseline metadata;
* monthly GF1 traces;
* exchange-rate labels;
* ETF terminology;
* gold unit;
* oil unit;
* optional missing TIPS;
* empty chart;
* invalid page response;
* route registration.

## Live validation

Inspect all three charts, tooltips, labels, narrower layout and other pages.

## Final response

Report implementation, tests, visual validation and limitations.

---

# Prompt 13 — Final Dashboard Integration, Consistency Review and Project Completion

Read `charts.md` in full.

All five analytical pages should now exist:

1. Macro Pulse
2. Monetary Policy & Liquidity
3. Housing Market & Consumer Credit
4. Financial Markets & Equities
5. Currency, Commodities & Fixed Income

This task is a controlled final integration and quality review.

Do not add major new analytical features.

## Objective

Turn the collection of completed pages into one coherent, production-quality version 1 dashboard.

## 1. Navigation

Update `src/api/dashboard/app.py` to include all pages.

Use restrained, consistent titles and icons.

Ensure:

* Home remains default;
* every page path exists;
* no unfinished page is exposed;
* navigation ordering matches `charts.md`.

## 2. Home navigation

Update the Home “Explore the dashboard” cards to link to the five actual analytical pages.

Remove obsolete categories such as:

* Growth and Activity;
* Inflation and Prices;
* Labour Market;
* Housing and Credit;
* Markets and Sterling;

where they no longer match the final page architecture.

Use:

* Macro Pulse;
* Monetary Policy & Liquidity;
* Housing Market & Consumer Credit;
* Financial Markets & Equities;
* Currency, Commodities & Fixed Income.

Remove “Coming soon” for completed pages.

Do not break Home card styling.

## 3. API integration

Confirm every router is registered in `src/api/main.py`.

Review route naming for consistency.

Do not rename stable routes unless necessary.

If route names differ, standardise endpoint-building configuration rather than scattering exceptions through page files.

## 4. Shared-code review

Review for:

* duplicated API-fetch functions;
* duplicated response validation;
* duplicated chart metadata rendering;
* duplicate KPI formatting;
* repeated Plotly layout code;
* repeated coverage handling;
* dead Macro Pulse compatibility code;
* obsolete debug routes;
* unused imports;
* duplicate gilt identifiers.

Refactor only where it clearly improves maintainability.

Do not perform broad speculative rewrites.

## 5. Visual consistency

Review all pages against Home and Macro Pulse.

Standardise:

* page-header spacing;
* KPI-card height;
* summary-panel placement;
* chart-container borders;
* chart height;
* legend placement;
* gridlines;
* hover formatting;
* section spacing;
* insight styling;
* methodology notes;
* empty states;
* mobile collapse behaviour.

Do not force identical layouts where chart needs differ.

## 6. Semantic colour review

Ensure repeated concepts use consistent colours where practical:

* Bank Rate;
* SONIA;
* CPI;
* core CPI;
* unemployment;
* FTSE 100;
* FTSE 250;
* sterling;
* Brent;
* WTI.

Avoid excessive red/green semantics.

Do not make a large design-system rewrite if shared constants are sufficient.

## 7. Data and analytical review

Check:

* correct units;
* correct dates;
* correct frequency labels;
* correct geography labels;
* price versus yield terminology;
* index versus percentage terminology;
* GBP versus USD denomination;
* no fabricated zeros;
* no unsupported causal statements;
* no daily forward-filled official monthly data presented as new information;
* no E&W/UK transaction mixing;
* all optional missing data disclosed clearly.

## 8. Failure-state review

For each page test:

* API unavailable;
* malformed response;
* one empty chart;
* missing optional series;
* missing summary;
* missing insight;
* partial metric coverage.

One optional chart failure should not destroy an otherwise valid page where the architecture supports partial rendering.

## 9. Performance review

Check:

* excessive database reads;
* repeated API calls per page;
* unnecessary full-history loading;
* expensive transformations performed in Streamlit;
* oversized JSON;
* Plotly rendering delays.

Optimise obvious issues without adding premature caching complexity.

Use Streamlit caching only if it fits existing application behaviour and does not conceal stale data.

## 10. Tests

Run the full test suite.

Add final integration tests for:

* all routers registered;
* all page modules import;
* navigation paths exist;
* chart config sections exist;
* chart IDs are unique;
* configured metrics resolve;
* page response chart order;
* Home links point to real pages.

Fix regressions caused by final integration.

Do not weaken tests merely to make them pass.

## 11. Live inspection

The app and Uvicorn may already be running.

Before starting services:

* check active processes;
* reuse running services;
* avoid duplicate ports;
* do not terminate unrelated Python processes.

Visually inspect:

* Home;
* Macro Pulse;
* Monetary Policy;
* Housing;
* Financial Markets;
* Global Flows.

Inspect desktop and narrow layouts.

Verify every navigation path.

Do not claim inspection that was not performed.

## 12. Documentation

Update README documentation with:

* product purpose;
* architecture;
* available pages;
* data sources;
* local setup;
* ETL/preparation command;
* FastAPI command;
* Streamlit command;
* testing command;
* known limitations;
* statement that analysis is descriptive and not financial advice.

Do not turn the README into a lengthy design specification; link to `charts.md` for detailed analytical requirements.

## 13. Definition of done

Version 1 is complete when:

* all five pages are accessible;
* all API routes return validated responses;
* all prepared datasets are reproducible;
* all charts have correct units and labels;
* Home navigation works;
* failure states are graceful;
* full tests pass;
* live pages have been inspected;
* documentation is current;
* remaining limitations are explicitly recorded.

## Non-goals

Do not add:

* forecasting;
* economic calendar;
* authentication;
* deployment infrastructure;
* LLM commentary;
* alerting;
* user accounts;
* advanced downloads;
* new data vendors;
* speculative indicators.

## Final response

Provide a completion report containing:

1. pages completed;
2. endpoints;
3. prepared datasets;
4. navigation updates;
5. shared refactors;
6. tests run and exact results;
7. live pages inspected;
8. known data limitations;
9. known technical limitations;
10. recommended future enhancements, clearly separated from version 1.
