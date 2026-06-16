# Remaining Calculation Build Brief

## Context

This project is a UK Economic Dashboard using:

* SQLite database: `economic_series.db`
* Main source table: `economic_series`
* Calculation module: `src/etl/build_calculations.py`
* Config loaded from: `calculations.yaml`
* Dashboard later built in Streamlit

The first calculation batch has already been started for monthly macro metrics and now also includes quarterly GDP.

Current function:

```python
macro_cols(config: dict, date_from=None)
```

This function loads selected `METRIC_ID`s from `economic_series`, pivots them wide by `DATE`, calculates derived columns, and returns a wide dataframe.

The remaining work is to clean up, complete, and save all calculation layers needed for the dashboard.

---

## Immediate Fixes Required

### 1. Fix config typo

Current config has:

```yaml
quarterly_gdp:
  GDP_QQQ:
    change_type: "pp"
  GDP_YOY:
    change_type: "pp"
```

This should be:

```yaml
quarterly_gdp:
  GDP_QOQ:
    change_type: "pp"
  GDP_YOY:
    change_type: "pp"
```

---

### 2. Fix `BUSINESS_CONF` indentation

Current config has broken indentation:

```yaml
BUSINESS_CONF:
change_type: "points"
```

Should be:

```yaml
BUSINESS_CONF:
  change_type: "points"
```

---

### 3. Treat lending flow metrics carefully

These two are monetary flow values and can be negative or close to zero:

```python
NET_LENDING_DWELLINGS_MO
NET_CONSUMER_CREDIT_MO
```

Do not rely on percentage change for dashboard display.

Set them as:

```yaml
NET_LENDING_DWELLINGS_MO:
  change_type: "flow"

NET_CONSUMER_CREDIT_MO:
  change_type: "flow"
```

For these, calculate percentage change if useful, but dashboard display should use raw value change:

```text
display_change = monthly £m change
display_yoy_change = YoY £m change
```

---

## Final Config Structure

Use one combined macro config for monthly and quarterly macro metrics.

Example:

```yaml
macro:
  CPI:
    change_type: "pp"
  CORE_CPI:
    change_type: "pp"
  UNRATE:
    change_type: "pp"
  EMPRATE:
    change_type: "pp"
  WAGE_GROWTH:
    change_type: "pp"
  HOUSE_PRICE_GROWTH:
    change_type: "pp"
  BUSINESS_CONF:
    change_type: "points"
  CONSUMER_CONF:
    change_type: "points"

  BANK_RATE_MO:
    change_type: "pp"
  MORTGAGE_2YR_75LTV_MO:
    change_type: "pp"
  M4_GROWTH_MO:
    change_type: "pp"
  NOTES_COINS_GROWTH_MO:
    change_type: "pp"
  NET_LENDING_CORP_MO:
    change_type: "pp"
  CORP_OVERDRAFT_COST_MO:
    change_type: "pp"
  NET_LENDING_DWELLINGS_MO:
    change_type: "flow"
  NET_CONSUMER_CREDIT_MO:
    change_type: "flow"
  STERLING_ERI_MO:
    change_type: "points"

  UK_HPI_AVG_PRICE_UK:
    change_type: "pct"
  UK_HPI_INDEX_UK:
    change_type: "pct"
  UK_HPI_AVG_PRICE_LONDON:
    change_type: "pct"
  UK_HPI_AVG_PRICE_NW:
    change_type: "pct"
  UK_HPI_VOLUME_UK:
    change_type: "pct"
  UK_HPI_FTB_AVG_PRICE:
    change_type: "pct"
  UK_HPI_FOO_AVG_PRICE:
    change_type: "pct"
  UK_HPI_CASH_AVG_PRICE:
    change_type: "pct"
  UK_HPI_MORTGAGE_AVG_PRICE:
    change_type: "pct"
  UK_HPI_CASH_SALES_VOL:
    change_type: "pct"
  UK_HPI_MORTGAGE_SALES_VOL:
    change_type: "pct"
  UK_HPI_YOY_CHANGE_UK:
    change_type: "pp"

  GDP_QOQ:
    change_type: "pp"
  GDP_YOY:
    change_type: "pp"
```

---

# Required Calculation Tables

The remaining calculations should create these final tables in SQLite:

```text
macro_calculations
daily_boe_calculations
market_calculations_daily
market_calculations_monthly
housing_derived_calculations
dashboard_snapshot
```

Build them in this order:

```text
1. macro_calculations
2. daily_boe_calculations
3. market_calculations_daily
4. market_calculations_monthly
5. housing_derived_calculations
6. dashboard_snapshot
```

---

# 1. `macro_calculations`

## Purpose

This table should contain calculated features for all monthly and quarterly macro metrics, including:

* ONS monthly metrics
* BoE monthly metrics
* HMLR monthly metrics
* GDP quarterly metrics

## Input

Source table:

```sql
economic_series
```

Input columns expected:

```text
DATE
METRIC_ID
VALUE
FREQUENCY
```

## Target metric IDs

```python
MACRO_METRICS = [
    # ONS monthly
    "CPI",
    "CORE_CPI",
    "UNRATE",
    "EMPRATE",
    "WAGE_GROWTH",
    "HOUSE_PRICE_GROWTH",
    "BUSINESS_CONF",
    "CONSUMER_CONF",

    # ONS quarterly
    "GDP_QOQ",
    "GDP_YOY",

    # BoE monthly
    "BANK_RATE_MO",
    "MORTGAGE_2YR_75LTV_MO",
    "M4_GROWTH_MO",
    "NOTES_COINS_GROWTH_MO",
    "NET_LENDING_CORP_MO",
    "CORP_OVERDRAFT_COST_MO",
    "NET_LENDING_DWELLINGS_MO",
    "NET_CONSUMER_CREDIT_MO",
    "STERLING_ERI_MO",

    # HMLR monthly
    "UK_HPI_AVG_PRICE_UK",
    "UK_HPI_INDEX_UK",
    "UK_HPI_AVG_PRICE_LONDON",
    "UK_HPI_AVG_PRICE_NW",
    "UK_HPI_VOLUME_UK",
    "UK_HPI_FTB_AVG_PRICE",
    "UK_HPI_FOO_AVG_PRICE",
    "UK_HPI_CASH_AVG_PRICE",
    "UK_HPI_MORTGAGE_AVG_PRICE",
    "UK_HPI_CASH_SALES_VOL",
    "UK_HPI_MORTGAGE_SALES_VOL",
    "UK_HPI_YOY_CHANGE_UK",
]
```

## Required columns

Prefer a long output format rather than a very wide dataframe.

Each row should represent one metric/date observation.

```text
DATE
METRIC_ID
VALUE
FREQUENCY
CHANGE_TYPE
PREVIOUS_VALUE
CHANGE
CHANGE_PCT
CHANGE_PP
ROLLING_3
ROLLING_12
VALUE_YEAR_AGO
YOY_CHANGE
YOY_CHANGE_PCT
YOY_CHANGE_PP
TREND
DISPLAY_CHANGE
DISPLAY_YOY_CHANGE
```

## Frequency logic

### Monthly metrics

For monthly metrics:

```python
year_ago_lag = 12
rolling_short_window = 3
rolling_long_window = 12
```

Calculations:

```python
PREVIOUS_VALUE = VALUE.shift(1)
CHANGE = VALUE - PREVIOUS_VALUE
CHANGE_PP = CHANGE
CHANGE_PCT = ((VALUE / PREVIOUS_VALUE) - 1) * 100

ROLLING_3 = VALUE.rolling(3, min_periods=3).mean()
ROLLING_12 = VALUE.rolling(12, min_periods=12).mean()

VALUE_YEAR_AGO = VALUE.shift(12)
YOY_CHANGE = VALUE - VALUE_YEAR_AGO
YOY_CHANGE_PP = YOY_CHANGE
YOY_CHANGE_PCT = ((VALUE / VALUE_YEAR_AGO) - 1) * 100
```

Trend:

```python
if ROLLING_3 > ROLLING_12:
    TREND = "Rising"
elif ROLLING_3 < ROLLING_12:
    TREND = "Falling"
else:
    TREND = "Flat"
```

If either rolling value is missing, set trend to `None`.

---

### Quarterly GDP metrics

For quarterly metrics:

```python
year_ago_lag = 4
rolling_short_window = 4
```

Calculations:

```python
PREVIOUS_VALUE = VALUE.shift(1)
CHANGE = VALUE - PREVIOUS_VALUE
CHANGE_PP = CHANGE
CHANGE_PCT = ((VALUE / PREVIOUS_VALUE) - 1) * 100

ROLLING_3 = None
ROLLING_12 = None
ROLLING_4Q = VALUE.rolling(4, min_periods=4).mean()

VALUE_YEAR_AGO = VALUE.shift(4)
YOY_CHANGE = VALUE - VALUE_YEAR_AGO
YOY_CHANGE_PP = YOY_CHANGE
YOY_CHANGE_PCT = ((VALUE / VALUE_YEAR_AGO) - 1) * 100
```

Trend for quarterly GDP:

```python
if VALUE > ROLLING_4Q:
    TREND = "Rising"
elif VALUE < ROLLING_4Q:
    TREND = "Falling"
else:
    TREND = "Flat"
```

If `ROLLING_4Q` is missing, set trend to `None`.

Either add a `ROLLING_4Q` column, or store it in `ROLLING_12` with clear naming. Preferred:

```text
ROLLING_4Q
```

So final macro table can include:

```text
ROLLING_4Q
```

---

## Change type display logic

Each metric has a `change_type`.

### `pp`

Used for rates and percentages.

```python
DISPLAY_CHANGE = CHANGE_PP
DISPLAY_YOY_CHANGE = YOY_CHANGE_PP
```

Examples:

```text
CPI
Bank Rate
Unemployment Rate
Mortgage Rate
GDP QoQ
GDP YoY
```

### `pct`

Used for prices, volumes, FX and index levels where percentage movement is useful.

```python
DISPLAY_CHANGE = CHANGE_PCT
DISPLAY_YOY_CHANGE = YOY_CHANGE_PCT
```

Examples:

```text
UK average house price
HPI index
sales volume
```

### `points`

Used for confidence/index indicators where raw point movement is better.

```python
DISPLAY_CHANGE = CHANGE
DISPLAY_YOY_CHANGE = YOY_CHANGE
```

Examples:

```text
Business confidence
Consumer confidence
Sterling ERI
```

### `flow`

Used for lending flow values that can be small, zero or negative.

```python
DISPLAY_CHANGE = CHANGE
DISPLAY_YOY_CHANGE = YOY_CHANGE
```

Examples:

```text
NET_LENDING_DWELLINGS_MO
NET_CONSUMER_CREDIT_MO
```

Still calculate `CHANGE_PCT` and `YOY_CHANGE_PCT`, but do not use them for dashboard display.

---

## Save output

Save to SQLite table:

```text
macro_calculations
```

Use `if_exists="replace"` for now.

---

# 2. `daily_boe_calculations`

## Purpose

Calculate daily rate movements for daily Bank of England series.

## Target metrics

```python
DAILY_BOE_METRICS = [
    "BANK_RATE_DA",
    "SONIA",
]
```

## Required columns

```text
DATE
METRIC_ID
VALUE
PREVIOUS_VALUE
CHANGE
CHANGE_PP
ROLLING_7D
ROLLING_30D
VALUE_30D_AGO
CHANGE_30D_PP
VALUE_365D_AGO
CHANGE_1Y_PP
DISPLAY_CHANGE
DISPLAY_30D_CHANGE
DISPLAY_1Y_CHANGE
```

## Calculations

For each `METRIC_ID`:

```python
PREVIOUS_VALUE = VALUE.shift(1)
CHANGE = VALUE - PREVIOUS_VALUE
CHANGE_PP = CHANGE

ROLLING_7D = VALUE.rolling(7, min_periods=7).mean()
ROLLING_30D = VALUE.rolling(30, min_periods=30).mean()

VALUE_30D_AGO = VALUE.shift(30)
CHANGE_30D_PP = VALUE - VALUE_30D_AGO

VALUE_365D_AGO = VALUE.shift(365)
CHANGE_1Y_PP = VALUE - VALUE_365D_AGO

DISPLAY_CHANGE = CHANGE_PP
DISPLAY_30D_CHANGE = CHANGE_30D_PP
DISPLAY_1Y_CHANGE = CHANGE_1Y_PP
```

Save to:

```text
daily_boe_calculations
```

---

# 3. Monthly resampling for daily BoE

## Purpose

Create monthly versions of daily BoE series so they can be compared with monthly macro data.

## Resampling rules

```python
BANK_RATE_DA -> month-end value
SONIA -> monthly average
```

Create monthly metric IDs:

```text
BANK_RATE_DA_MONTHLY
SONIA_MONTHLY_AVG
```

For these resampled series, apply the same monthly macro calculation logic used in `macro_calculations`.

Options:

1. Add these rows into `macro_calculations`
2. Or create separate table `boe_monthly_resampled_calculations`

Preferred for simplicity:

```text
append to macro_calculations
```

with clear `METRIC_ID`s:

```text
BANK_RATE_DA_MONTHLY
SONIA_MONTHLY_AVG
```

Both should have:

```yaml
change_type: "pp"
```

---

# 4. `market_calculations_daily`

## Purpose

Calculate daily Yahoo Finance market features.

## Target Yahoo metrics

```python
YAHOO_METRICS = [
    "GILT_CORE",
    "FX_GBP_USD",
    "FX_GBP_EUR",
    "FX_GBP_JPY",
    "FX_GBP_CHF",
    "FX_GBP_AUD",
    "FX_GBP_CAD",
    "FTSE_100",
    "FTSE_250",
    "FTSE_AIM",
    "FTSE_ALL_SHARE",
    "TSCO_L",
    "SBRY_L",
    "BA_L",
    "RR_L",
    "SGE_L",
    "VPNG_L",
    "ETF_UK_HIGH_YIELD",
    "ETF_UK_GILT",
    "ETF_UK_TIPS",
    "ETF_UK_CORP_BOND",
    "EQ_TW",
    "EQ_BARC",
    "EQ_RIO",
    "EQ_BP",
    "EQ_GSK",
    "EQ_BAR",
    "COM_OIL_WTI",
    "COM_OIL_BRENT",
    "COM_GOLD",
]
```

## Input columns expected

From `economic_series` or Yahoo-specific raw table:

```text
DATE
METRIC_ID
OPEN
HIGH
LOW
CLOSE
ADJ_CLOSE
VOLUME
```

If `ADJ_CLOSE` is missing, use `CLOSE`.

Create:

```python
PRICE_FOR_RETURNS = ADJ_CLOSE.fillna(CLOSE)
```

## Required columns

```text
DATE
METRIC_ID
OPEN
HIGH
LOW
CLOSE
ADJ_CLOSE
VOLUME
PRICE_FOR_RETURNS
PREVIOUS_CLOSE
RETURN_1D
RETURN_5D
RETURN_21D
RETURN_63D
RETURN_126D
RETURN_252D
RETURN_YTD
MA_20
MA_50
MA_200
ROLLING_52W_HIGH
DRAWDOWN_52W
ROLLING_VOL_30D
```

## Calculations

For each `METRIC_ID`:

```python
PREVIOUS_CLOSE = PRICE_FOR_RETURNS.shift(1)

RETURN_1D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(1) - 1) * 100
RETURN_5D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(5) - 1) * 100
RETURN_21D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(21) - 1) * 100
RETURN_63D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(63) - 1) * 100
RETURN_126D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(126) - 1) * 100
RETURN_252D = (PRICE_FOR_RETURNS / PRICE_FOR_RETURNS.shift(252) - 1) * 100
```

YTD:

```python
YEAR = DATE.dt.year
FIRST_PRICE_OF_YEAR = first PRICE_FOR_RETURNS per METRIC_ID/YEAR
RETURN_YTD = (PRICE_FOR_RETURNS / FIRST_PRICE_OF_YEAR - 1) * 100
```

Moving averages:

```python
MA_20 = PRICE_FOR_RETURNS.rolling(20, min_periods=20).mean()
MA_50 = PRICE_FOR_RETURNS.rolling(50, min_periods=50).mean()
MA_200 = PRICE_FOR_RETURNS.rolling(200, min_periods=200).mean()
```

52-week drawdown:

```python
ROLLING_52W_HIGH = PRICE_FOR_RETURNS.rolling(252, min_periods=252).max()
DRAWDOWN_52W = (PRICE_FOR_RETURNS / ROLLING_52W_HIGH - 1) * 100
```

30-day volatility:

```python
DAILY_RETURN_DECIMAL = PRICE_FOR_RETURNS.pct_change()
ROLLING_VOL_30D = DAILY_RETURN_DECIMAL.rolling(30, min_periods=30).std() * np.sqrt(252) * 100
```

Save to:

```text
market_calculations_daily
```

---

# 5. `market_calculations_monthly`

## Purpose

Convert daily Yahoo data to monthly dashboard-ready data.

## Aggregation

For each `METRIC_ID` and month:

```python
MONTHLY_CLOSE = last CLOSE in month
MONTHLY_ADJ_CLOSE = last ADJ_CLOSE in month
MONTHLY_PRICE_FOR_RETURNS = last PRICE_FOR_RETURNS in month
MONTHLY_VOLUME = sum VOLUME in month
```

## Required columns

```text
DATE
METRIC_ID
MONTHLY_CLOSE
MONTHLY_ADJ_CLOSE
MONTHLY_PRICE_FOR_RETURNS
MONTHLY_VOLUME
RETURN_1M
RETURN_3M
RETURN_6M
RETURN_12M
RETURN_YTD
ROLLING_3M
ROLLING_12M
TREND
```

## Calculations

For each `METRIC_ID`:

```python
RETURN_1M = (MONTHLY_PRICE_FOR_RETURNS / MONTHLY_PRICE_FOR_RETURNS.shift(1) - 1) * 100
RETURN_3M = (MONTHLY_PRICE_FOR_RETURNS / MONTHLY_PRICE_FOR_RETURNS.shift(3) - 1) * 100
RETURN_6M = (MONTHLY_PRICE_FOR_RETURNS / MONTHLY_PRICE_FOR_RETURNS.shift(6) - 1) * 100
RETURN_12M = (MONTHLY_PRICE_FOR_RETURNS / MONTHLY_PRICE_FOR_RETURNS.shift(12) - 1) * 100
```

YTD:

```python
YEAR = DATE.dt.year
FIRST_MONTHLY_PRICE_OF_YEAR = first MONTHLY_PRICE_FOR_RETURNS per METRIC_ID/YEAR
RETURN_YTD = (MONTHLY_PRICE_FOR_RETURNS / FIRST_MONTHLY_PRICE_OF_YEAR - 1) * 100
```

Trend:

```python
ROLLING_3M = MONTHLY_PRICE_FOR_RETURNS.rolling(3, min_periods=3).mean()
ROLLING_12M = MONTHLY_PRICE_FOR_RETURNS.rolling(12, min_periods=12).mean()

if ROLLING_3M > ROLLING_12M:
    TREND = "Rising"
elif ROLLING_3M < ROLLING_12M:
    TREND = "Falling"
else:
    TREND = "Flat"
```

If either rolling value is missing, set `TREND = None`.

Save to:

```text
market_calculations_monthly
```

---

# 6. `housing_derived_calculations`

## Purpose

Create useful housing dashboard ratios from HMLR metrics.

## Derived metrics

Create these metric IDs:

```python
HOUSING_DERIVED_METRICS = {
    "LONDON_PRICE_PREMIUM": "London avg price / UK avg price",
    "NW_PRICE_RATIO": "North West avg price / UK avg price",
    "CASH_BUYER_SHARE": "Cash sales volume / total sales volume",
    "MORTGAGE_BUYER_SHARE": "Mortgage sales volume / total sales volume",
    "FTB_PRICE_RATIO": "First-time buyer avg price / UK avg price",
    "CASH_VS_MORTGAGE_PRICE_RATIO": "Cash avg price / mortgage avg price",
}
```

## Formulas

For each month:

```python
LONDON_PRICE_PREMIUM = UK_HPI_AVG_PRICE_LONDON / UK_HPI_AVG_PRICE_UK

NW_PRICE_RATIO = UK_HPI_AVG_PRICE_NW / UK_HPI_AVG_PRICE_UK

CASH_BUYER_SHARE = (UK_HPI_CASH_SALES_VOL / UK_HPI_VOLUME_UK) * 100

MORTGAGE_BUYER_SHARE = (UK_HPI_MORTGAGE_SALES_VOL / UK_HPI_VOLUME_UK) * 100

FTB_PRICE_RATIO = UK_HPI_FTB_AVG_PRICE / UK_HPI_AVG_PRICE_UK

CASH_VS_MORTGAGE_PRICE_RATIO = UK_HPI_CASH_AVG_PRICE / UK_HPI_MORTGAGE_AVG_PRICE
```

## Then calculate standard monthly changes

For each derived metric, calculate:

```text
PREVIOUS_VALUE
CHANGE
CHANGE_PCT
CHANGE_PP
ROLLING_3
ROLLING_12
VALUE_YEAR_AGO
YOY_CHANGE
YOY_CHANGE_PCT
YOY_CHANGE_PP
TREND
DISPLAY_CHANGE
DISPLAY_YOY_CHANGE
```

## Display logic

Use:

```yaml
LONDON_PRICE_PREMIUM:
  change_type: "pct"
NW_PRICE_RATIO:
  change_type: "pct"
CASH_BUYER_SHARE:
  change_type: "pp"
MORTGAGE_BUYER_SHARE:
  change_type: "pp"
FTB_PRICE_RATIO:
  change_type: "pct"
CASH_VS_MORTGAGE_PRICE_RATIO:
  change_type: "pct"
```

Latest value display formatting later:

```text
LONDON_PRICE_PREMIUM -> 1.82x
NW_PRICE_RATIO -> 0.74x
CASH_BUYER_SHARE -> 26.7%
MORTGAGE_BUYER_SHARE -> 63.4%
FTB_PRICE_RATIO -> 0.84x
```

Save to:

```text
housing_derived_calculations
```

---

# 7. `dashboard_snapshot`

## Purpose

Create one latest row per key metric for Streamlit KPI cards.

## Input tables

Pull latest rows from:

```text
macro_calculations
market_calculations_monthly
housing_derived_calculations
```

## Snapshot metric list

```python
SNAPSHOT_METRICS = [
    # macro
    "CPI",
    "CORE_CPI",
    "GDP_QOQ",
    "GDP_YOY",
    "UNRATE",
    "WAGE_GROWTH",
    "BANK_RATE_MO",
    "SONIA_MONTHLY_AVG",
    "MORTGAGE_2YR_75LTV_MO",
    "UK_HPI_YOY_CHANGE_UK",
    "UK_HPI_AVG_PRICE_UK",
    "UK_HPI_VOLUME_UK",
    "NET_LENDING_DWELLINGS_MO",
    "CONSUMER_CONF",
    "BUSINESS_CONF",

    # housing derived
    "LONDON_PRICE_PREMIUM",
    "CASH_BUYER_SHARE",
    "MORTGAGE_BUYER_SHARE",

    # markets
    "FTSE_100",
    "FTSE_250",
    "FTSE_AIM",
    "FX_GBP_USD",
    "FX_GBP_EUR",
    "ETF_UK_GILT",
    "ETF_UK_HIGH_YIELD",
    "COM_OIL_BRENT",
    "COM_GOLD",
]
```

## Required columns

```text
METRIC_ID
METRIC_NAME
CATEGORY
SOURCE_TABLE
LATEST_DATE
LATEST_VALUE
UNIT
DISPLAY_CHANGE
DISPLAY_YOY_CHANGE
TREND
```

For market metrics, map:

```text
LATEST_VALUE = MONTHLY_PRICE_FOR_RETURNS
DISPLAY_CHANGE = RETURN_1M
DISPLAY_YOY_CHANGE = RETURN_12M
```

For macro metrics, use:

```text
LATEST_VALUE = VALUE
DISPLAY_CHANGE = DISPLAY_CHANGE
DISPLAY_YOY_CHANGE = DISPLAY_YOY_CHANGE
```

For housing derived metrics, use:

```text
LATEST_VALUE = VALUE
DISPLAY_CHANGE = DISPLAY_CHANGE
DISPLAY_YOY_CHANGE = DISPLAY_YOY_CHANGE
```

Save to:

```text
dashboard_snapshot
```

---

# Build Order

Complete the remaining work in this exact order:

```text
1. Fix config issues
2. Refactor macro calculation output to long format
3. Save macro_calculations
4. Build daily_boe_calculations
5. Resample daily BoE into monthly and append to macro_calculations
6. Build market_calculations_daily
7. Build market_calculations_monthly
8. Build housing_derived_calculations
9. Build dashboard_snapshot
10. Add simple validation checks
```

---

# Validation Checks

Add validation after each table is built.

## General checks

```python
assert not df.empty
assert df["DATE"].notna().all()
assert df["METRIC_ID"].notna().all()
```

## Duplicate check

```python
duplicates = df[df.duplicated(["DATE", "METRIC_ID"], keep=False)]
assert duplicates.empty
```

## Macro sanity checks

For `CPI`:

```text
DISPLAY_CHANGE should equal CHANGE_PP
DISPLAY_YOY_CHANGE should equal YOY_CHANGE_PP
```

For `UK_HPI_AVG_PRICE_UK`:

```text
DISPLAY_CHANGE should equal CHANGE_PCT
DISPLAY_YOY_CHANGE should equal YOY_CHANGE_PCT
```

For `NET_LENDING_DWELLINGS_MO`:

```text
DISPLAY_CHANGE should equal CHANGE
DISPLAY_YOY_CHANGE should equal YOY_CHANGE
```

## Market sanity checks

For each market metric:

```text
RETURN_1D should be null on first row
MA_200 should be null until 200 observations exist
DRAWDOWN_52W should be <= 0
```

## Snapshot sanity checks

```text
one row per METRIC_ID
LATEST_DATE should not be null
LATEST_VALUE should not be null
```

---

# Notes For Implementation

* Prefer long tables for final saved calculation outputs.
* Wide dataframes are fine internally for calculations, but save final outputs long.
* Keep raw source tables untouched.
* Use `if_exists="replace"` while developing.
* Later, this can be changed to incremental updates.
* Do not start Streamlit pages until all calculation tables are created and validated.
