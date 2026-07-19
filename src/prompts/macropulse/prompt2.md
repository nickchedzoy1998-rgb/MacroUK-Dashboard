# Prompt 2 — Prepare the Macro Pulse Data Layer

Read `charts.md` in full before making changes.

The shared analytical dashboard foundation should already exist from the previous task.

This task is limited to preparing the datasets and deterministic analytical calculations required by the Macro Pulse page.

Do not implement the final FastAPI response contract or Streamlit page in this change unless a minimal adjustment is essential to validate the prepared data.

## Objective

Create reproducible, tested, chart-oriented data preparation for:

1. Economic Growth Momentum
2. Inflation Pressures
3. Labour Market Health
4. Macro Pulse headline KPIs
5. Macro Pulse deterministic summary and chart insights, if the project’s architecture places these calculations in the preparation or service layer

The prepared output should be suitable for a later API task without requiring substantial transformation in Streamlit.

---

## Before changing code

Inspect:

* current ETL and calculation modules;
* SQLite table structure;
* existing chart-data preparation;
* `charts` configuration;
* actual available metric identifiers;
* Home summary-generation architecture;
* tests for data preparation;
* how preparation tasks are run;
* current `macro_pulse.py`;
* current API chart routes.

Do not assume metric names from `charts.md` are all exact.

Verify them against:

* configuration;
* database records;
* ETL source definitions;
* existing code.

Report any missing or mismatched metric explicitly.

---

## 1. Confirm the actual Macro Pulse metrics

The intended chart concepts are:

### Growth

* `GDP_QOQ`
* `GDP_YOY`

### Inflation

* `CPI`
* `CORE_CPI`
* a genuine housing-cost or housing-related inflation measure, if one exists

### Labour

* `UNRATE`
* `EMPRATE`
* `WAGE_GROWTH`

Important:

Do not use annual house-price growth as though it were housing-cost inflation.

If no appropriate housing-cost inflation series exists:

* do not fabricate or silently substitute one;
* prepare the chart with CPI and core CPI only;
* expose the missing optional series in metadata or document it clearly;
* preserve an architecture that can accept it later.

---

## 2. Prepared dataset design

Follow existing repository conventions.

Prefer either:

* one prepared table per chart;
* or one clearly structured Macro Pulse prepared table if that matches the current architecture.

Do not create a needlessly generic warehouse model.

The prepared data must be:

* sorted;
* reproducible;
* typed consistently;
* free from accidental duplicates;
* stored through the existing SQLite workflow;
* suitable for API serialization;
* explicit about frequency.

Suggested logical outputs are below.

### A. Growth dataset

Fields should include the equivalent of:

```text
date
GDP_QOQ
GDP_YOY
```

or a long-format equivalent.

Requirements:

* retain quarterly frequency;
* do not resample to monthly;
* use a consistent quarter-end or official observation date convention;
* include only valid observations;
* preserve negative values;
* make missing GDP_QOQ or GDP_YOY visible rather than converting to zero.

### B. Inflation dataset

Fields should include the equivalent of:

```text
date
CPI
CORE_CPI
optional_housing_inflation
```

Requirements:

* monthly frequency;
* align by actual month;
* do not forward-fill missing releases;
* retain the 2% policy target as metadata or interpretation configuration rather than a fake data series, unless the existing chart system expects reference-line data.

### C. Labour dataset

Fields should include the equivalent of:

```text
date
UNRATE
EMPRATE
WAGE_GROWTH
```

Requirements:

* monthly frequency;
* preserve actual available observation dates or convert to a consistent monthly date convention;
* do not assume all three series begin or end on the same month;
* maintain nulls where one series is unavailable;
* do not forward-fill by default.

---

## 3. Macro Pulse KPIs

Prepare the values required for three or four top-of-page indicators.

Recommended default set:

1. quarterly GDP growth;
2. headline CPI inflation;
3. unemployment rate;
4. wage growth.

The exact set may follow configuration if already established.

Each KPI should support:

```text
metric identifier
display name
latest value
latest date
delta
delta comparison label
main unit
delta unit
description
delta direction
```

Reuse Home KPI preparation logic where practical.

Do not create a second incompatible KPI system.

Suggested comparisons:

* GDP_QOQ: latest value, with previous-quarter change only if analytically useful;
* CPI: change from previous monthly observation or distance from 2% target, depending on existing configuration;
* UNRATE: previous monthly observation, with inverse direction semantics;
* WAGE_GROWTH: previous monthly observation.

Keep comparisons explicit.

---

## 4. Deterministic page summary

Create a deterministic Macro Pulse overview using the latest available values.

The output should support:

```python
{
    "headline": "...",
    "body": "..."
}
```

The summary should combine:

* growth state;
* inflation state;
* labour-market direction.

Use cautious wording.

### Growth states

Using GDP_QOQ:

* below 0: contraction;
* 0 to 0.1: broadly flat;
* above 0.1 to 0.5: modest growth;
* above 0.5: stronger growth.

### Inflation states

Using CPI against the configured target:

* materially above target;
* moderately above target;
* near target;
* below target.

Use project-consistent thresholds and place them in named constants or configuration rather than hiding them in deeply nested conditions.

### Labour states

Use recent changes in unemployment, employment and wage growth.

Suitable wording:

* labour conditions are softening;
* labour conditions remain broadly stable;
* wage growth is easing;
* wage growth remains elevated.

Avoid:

* “wage-price spiral”;
* causal claims;
* predictions about Bank of England policy;
* claims of historic strength or weakness without explicit historical calculations.

The summary must still work when one component is unavailable.

---

## 5. Chart-specific deterministic insights

Prepare one concise insight per chart where the available data supports it.

Suggested structure:

```python
{
    "chart_id": "EGM",
    "headline": "...",
    "body": "...",
    "direction": "positive" | "negative" | "neutral",
    "as_of_date": "YYYY-MM-DD"
}
```

### Growth insight

May describe:

* latest quarter as expansion, contraction or flat;
* whether annual growth is strengthening or weakening compared with the previous observation.

### Inflation insight

May describe:

* CPI’s distance from target;
* whether core inflation is above or below headline inflation;
* whether both are rising or easing.

Do not describe inflation as broadening from only one observation.

### Labour insight

May describe:

* unemployment direction;
* employment direction;
* wage-growth direction.

Avoid assigning a positive or negative direction where the signal is genuinely mixed.

---

## 6. Configuration

Update `charts` configuration only where needed.

The Macro Pulse section should contain stable metadata such as:

* chart names;
* descriptions;
* metrics;
* frequency;
* chart type;
* units;
* optional target;
* display order.

Correct inaccurate configuration.

For example, do not leave `HOUSE_PRICE_GROWTH` configured as an inflation metric if it is not an inflation series.

Do not put generated current-state text in YAML.

---

## 7. Data quality and coverage

For each chart dataset, calculate or expose:

* requested metrics;
* metrics present;
* metrics missing;
* first observation per metric;
* latest observation per metric;
* valid row counts.

Use the shared coverage helper if available.

Preparation should fail clearly for missing required metrics.

An optional missing housing-inflation series should not prevent CPI and core CPI from being prepared.

---

## 8. Tests

Add targeted tests for:

### Growth

* quarterly frequency retained;
* negative GDP values preserved;
* dates sorted;
* missing values not converted to zero.

### Inflation

* CPI and core CPI aligned monthly;
* target available to interpretation logic;
* missing optional housing inflation handled safely;
* house-price growth is not silently substituted.

### Labour

* three series align without forced filling;
* partial coverage preserved;
* latest observation selected correctly.

### KPI preparation

* correct latest values;
* correct delta semantics;
* inverse unemployment direction;
* missing previous observation.

### Summary logic

* GDP contraction;
* GDP broadly flat;
* modest growth;
* inflation above target;
* inflation near target;
* unemployment rising;
* wage growth easing;
* missing one component.

### Insights

* chart IDs correct;
* mixed labour signals produce neutral wording where appropriate;
* no unsupported claim generated from missing data.

Avoid tests that assert entire paragraphs where smaller semantic assertions are more robust.

---

## 9. Non-goals

Do not:

* build the final Macro Pulse API schema;
* build the Streamlit charts;
* redesign Home;
* implement another analytical page;
* add new external data sources;
* substitute unavailable data without approval;
* forward-fill quarterly GDP to monthly dates;
* place core transformation logic in Streamlit.

---

## 10. Validation

After implementation:

1. Run the Macro Pulse preparation process.
2. Inspect the resulting SQLite table or tables.
3. Confirm GDP remains quarterly.
4. Confirm inflation and labour remain monthly.
5. Confirm missing optional metrics are reported clearly.
6. Confirm current values match the source table.
7. Run targeted tests.
8. Run relevant existing tests.
9. Check whether current Uvicorn or Streamlit processes are already active before starting anything.
10. Do not alter running services unnecessarily.

## Final response

Summarise:

* actual metric identifiers found;
* any intended metric that was unavailable;
* prepared tables created or modified;
* preparation and insight logic added;
* configuration changes;
* tests and results;
* assumptions;
* anything the API implementation must account for.
