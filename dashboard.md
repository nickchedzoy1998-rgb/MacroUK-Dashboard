# UK Economic Dashboard — Project Brief

## Objective

Build a portfolio-quality UK economic dashboard using Python, SQLite, GitHub Actions and Streamlit.

The dashboard should show the state of the UK economy using macroeconomic, monetary, housing and market data from:

* Office for National Statistics
* Bank of England
* Yahoo Finance
* HM Land Registry

The goal is not to build a full professional macro terminal. The goal is to build a clean, automated, explainable analytics project that demonstrates:

* API/data ingestion
* SQLite database design
* data cleaning and transformation
* calculated metrics
* Streamlit dashboarding
* scheduled data refreshes
* economic interpretation

---

## Current Setup

Metrics are already being saved into:

```text
economic_series.db
```

This database should remain the central data store.

The project should now focus on:

1. Cleaning and standardising the stored data
2. Creating calculated analytics tables
3. Building a Streamlit dashboard from those tables
4. Automating refreshes with GitHub Actions

---

## Recommended Project Structure

```text
uk-economic-dashboard/
│
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   │   ├── 1_UK_Overview.py
│   │   ├── 2_Inflation_and_Rates.py
│   │   ├── 3_Housing_and_Credit.py
│   │   ├── 4_Markets.py
│   │   └── 5_Data_Explorer.py
│   │
│   ├── components/
│   │   ├── kpi_cards.py
│   │   ├── charts.py
│   │   └── tables.py
│
├── scripts/
│   ├── fetch_ons.py
│   ├── fetch_boe.py
│   ├── fetch_yahoo.py
│   ├── fetch_hmlr.py
│   ├── build_calculations.py
│   └── run_pipeline.py
│
├── config/
│   └── metrics.yaml
│
├── data/
│   └── economic_series.db
│
├── .github/
│   └── workflows/
│       └── update_data.yml
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Database Plan

Use SQLite.

Keep raw/source data and calculated dashboard data separate.

### Existing/raw tables

These may already exist or can be adapted:

```text
ons_series
boe_series
yahoo_series
hmlr_series
```

Each should broadly include:

```text
date
metric_code
metric_name
value
source
unit
frequency
last_updated
```

For Yahoo market data, include:

```text
date
metric_code
ticker
open
high
low
close
adj_close
volume
source
last_updated
```

---

## New Calculation Tables To Create

### 1. `macro_calculations`

For ONS, BoE and HMLR metrics.

Columns:

```text
date
metric_code
metric_name
category
value
unit
frequency
previous_value
change
change_pct
change_pp
mom_change
yoy_change
rolling_3m
rolling_12m
trend
```

Use:

* `change_pp` for percentages/rates, e.g. CPI, Bank Rate, unemployment
* `change_pct` for levels, e.g. house prices, lending, sales volume

---

### 2. `market_calculations`

For Yahoo Finance data.

Columns:

```text
date
metric_code
ticker
metric_name
category
close
adj_close
volume
return_1d
return_5d
return_1m
return_3m
return_6m
return_1y
return_ytd
ma_50
ma_200
drawdown_52w
```

Use `adj_close` for return calculations where available.

Use `close` for displayed spot prices such as FX, oil, gold and indices.

---

### 3. `dashboard_snapshot`

One latest row per key metric.

This powers the KPI cards.

Columns:

```text
metric_code
metric_name
category
latest_date
latest_value
previous_value
change
change_pct
change_pp
unit
trend
status
```

Example statuses:

```text
Rising
Falling
Flat
Improving
Deteriorating
Mixed
Elevated
Low
```

Keep the status logic simple and transparent.

---

## Core Calculations

### Macro calculations

For each macro metric:

```text
latest value
previous value
absolute change
percentage change
percentage point change
month-on-month change
year-on-year change
3-month rolling average
12-month rolling average
trend
```

### Market calculations

For each Yahoo metric:

```text
1D return
5D return
1M return
3M return
6M return
1Y return
YTD return
50-day moving average
200-day moving average
52-week drawdown
```

### Housing-specific calculations

Create these if the source data is available:

```text
London premium = London average price / UK average price

North West discount/premium = North West average price / UK average price

Cash buyer share = cash sales volume / total sales volume

Mortgage buyer share = mortgage sales volume / total sales volume

FTB price ratio = first-time buyer average price / UK average house price
```

These are simple and give the dashboard more original analysis.

---

## Streamlit Dashboard Pages

Build four main pages first.

A fifth data explorer page can be added once the main pages are working.

---

## Page 1 — UK Overview

Purpose:

Show the current state of the UK economy on one page.

### KPI cards

Use:

```text
CPI
Core CPI
GDP QoQ
Unemployment Rate
Wage Growth
Bank Rate
Mortgage Rate
UK House Price YoY
FTSE 250
GBP/USD
```

### Charts

```text
Inflation vs Bank Rate
GDP / Labour Market Snapshot
House Prices vs Mortgage Rate
FTSE 100 vs FTSE 250 indexed to 100
```

### Extra widgets

```text
Top improving metrics
Top deteriorating metrics
Latest market movers
```

Keep these as simple tables.

---

## Page 2 — Inflation & Rates

Purpose:

Show whether inflation pressure is rising or falling and how restrictive monetary policy is.

### KPI cards

```text
CPI
Core CPI
Wage Growth
Bank Rate
SONIA
Mortgage Rate
Brent Oil
GBP/USD
```

### Charts

```text
CPI vs Core CPI
CPI vs Wage Growth
Bank Rate vs SONIA
Bank Rate vs Mortgage Rate
Brent Oil vs GBP/USD
```

---

## Page 3 — Housing & Credit

Purpose:

Show the condition of the housing market and household/credit stress.

### KPI cards

```text
UK Average House Price
UK HPI YoY Change
London Average Price
North West Average Price
Sales Volume
Mortgage Rate
Net Mortgage Lending
Consumer Credit
Cash Buyer Share
```

### Charts

```text
UK vs London vs North West house prices
House price growth vs mortgage rate
Sales volume vs mortgage lending
Cash sales vs mortgage sales
Consumer credit vs consumer confidence
```

This should be one of the strongest pages because the data is intuitive and visually clear.

---

## Page 4 — Markets

Purpose:

Show what financial markets are pricing about the UK economy.

### KPI cards

```text
FTSE 100
FTSE 250
FTSE AIM
GBP/USD
GBP/EUR
Gilt ETF
High Yield ETF
Gold
Brent Oil
```

### Charts

```text
FTSE 100 vs FTSE 250 vs AIM indexed to 100
Sterling FX basket indexed to 100
Gilt ETF vs Corporate Bond ETF vs High Yield ETF
Brent vs WTI vs Gold
```

### Market table

Create a table with:

```text
Metric
Latest
1D Return
5D Return
1M Return
3M Return
YTD Return
1Y Return
52W Drawdown
```

---

## Optional Page 5 — Data Explorer

Add after the main dashboard is complete.

Features:

```text
Metric selector
Date range selector
Line chart
Raw/calculated data table
Download option
```

This is useful for portfolio value because it shows reusable interactive analysis.

---

## Streamlit Components

Use simple reusable components.

### KPI card component

Input:

```text
metric_code
latest_value
change
unit
trend
status
```

Output:

```text
st.metric()
```

### Chart component

Reusable functions for:

```text
line chart
indexed line chart
bar chart
comparison chart
```

### Table component

Reusable functions for:

```text
market returns table
top movers table
latest metrics table
```

---

## Recommended Tech Stack

```text
Python
Pandas
SQLite
SQLAlchemy or sqlite3
Streamlit
Plotly
Yahoo Finance / yfinance
Requests
PyYAML
GitHub Actions
```

Use Plotly for charts rather than relying only on native Streamlit charts.

---

## GitHub Actions Plan

Run the full pipeline once per day or once per week.

For a portfolio project, daily is fine but not essential.

Workflow:

```text
1. Checkout repo
2. Set up Python
3. Install requirements
4. Run scripts/run_pipeline.py
5. Commit updated economic_series.db back to repo
```

The pipeline should:

```text
fetch latest data
update raw tables
rebuild calculation tables
rebuild dashboard_snapshot
```

---

## Build Order

### Phase 1 — Confirm database structure

Check that all source metrics are being saved correctly into `economic_series.db`.

Validate:

```text
dates are correct
metric codes are consistent
values are numeric
duplicates are handled
latest values are available
Yahoo data has OHLCV fields
```

---

### Phase 2 — Build calculation script

Create:

```text
scripts/build_calculations.py
```

This should:

```text
load raw/source tables from SQLite
calculate macro changes
calculate market returns
calculate housing ratios
create dashboard_snapshot
save calculation tables back to SQLite
```

---

### Phase 3 — Build UK Overview page

Start with only:

```text
10 KPI cards
4 charts
1 market movers table
```

Do not build the other pages until the overview works.

---

### Phase 4 — Build remaining pages

Build in this order:

```text
Inflation & Rates
Housing & Credit
Markets
Data Explorer
```

---

### Phase 5 — Polish for portfolio

Add:

```text
clean README
screenshots
data source explanation
dashboard methodology
GitHub Actions badge
deployed Streamlit link
```

README should explain:

```text
what the project does
which data sources are used
how the pipeline works
what calculations are performed
how to run locally
how the dashboard is structured
future improvements
```

---

## What To Avoid In Version 1

Do not build yet:

```text
FastAPI backend
complex macro regime scoring
machine learning
advanced z-score engines
full alert database
too many pages
too many charts
over-complicated economic commentary
```

These can be future improvements.

The priority is a finished, clean, automated dashboard.

---

## Final MVP Scope

The finished MVP should include:

```text
SQLite database: economic_series.db
Automated data ingestion
Calculation tables
Streamlit dashboard
4 main pages
KPI cards
Line charts
Indexed market charts
Market returns table
Housing ratios
GitHub Actions scheduled refresh
Clear README
Deployed app
```

---

## Project Positioning

This should be presented as:

```text
A Python-based UK economic dashboard that automatically collects macroeconomic, monetary, housing and financial market data, stores it in SQLite, builds calculated analytics tables, and visualises the results in an interactive Streamlit app.
```

The project demonstrates:

```text
data engineering
API integration
database design
analytics calculations
dashboard development
automation
economic interpretation
```

The key is not maximum complexity.

The key is:

```text
clean pipeline
clear calculations
usable dashboard
finished deployment
good explanation
```
