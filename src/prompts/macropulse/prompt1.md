# Prompt 1 — Build the Shared Analytical Dashboard Foundation

Read `charts.md` in full before making changes.

The Home page is already complete and establishes the target visual standard for the rest of the dashboard. This task is to create the reusable analytical foundation that the five remaining pages will use.

Do not implement or redesign any complete analytical page in this change.

## Objective

Create the shared utilities, components, styles and tests required to support professional analytical pages without duplicating logic across:

1. Macro Pulse
2. Monetary Policy & Liquidity
3. Housing Market & Consumer Credit
4. Financial Markets & Equities
5. Currency, Commodities & Fixed Income

The result should provide a stable base for later page-specific prompts.

## Before changing code

Inspect the repository and identify:

* the current dashboard folder structure;
* the charting library already used, if any;
* existing date, API and configuration utilities;
* existing prepared-data conventions;
* existing test structure;
* how Home injects external CSS;
* whether any chart transformation helpers already exist;
* whether Streamlit and Uvicorn are already running.

Reuse existing conventions where they are sound.

Do not create duplicate helpers simply because their current names differ from the names suggested below.

## Scope

Implement only the shared foundation described below.

---

## 1. Shared time-series transformation utilities

Create or extend a project-appropriate utility module for reusable chart transformations.

The exact location should follow repository conventions. A suitable example might be:

```text
src/analytics/chart_transforms.py
```

or:

```text
src/utilities/chart_transforms.py
```

Implement small, focused, typed functions for the following.

### A. Date preparation

A helper that:

* converts a date column to datetime;
* removes or handles invalid dates intentionally;
* sorts observations ascending;
* supports configurable date-column names;
* does not mutate the caller’s DataFrame unless clearly documented.

### B. Duplicate handling

A helper or clearly documented internal rule for duplicate observations.

The behaviour must be explicit.

Do not silently average duplicate economic observations unless that is clearly appropriate.

Possible supported behaviours may include:

* keep last;
* keep first;
* raise an error.

Use the safest project-appropriate default.

### C. First-common-date normalisation

Create a helper that rebases multiple series to:

```text
100 at the first common valid observation
```

Requirements:

* work with a long-format DataFrame where practical;
* identify the first date on which all requested series have valid values;
* return the effective baseline date;
* return normalised values;
* preserve original values where useful;
* handle missing series cleanly;
* fail clearly or return a documented empty result when no common baseline exists;
* never divide by zero.

### D. Cumulative percentage return

Create a helper that calculates:

```text
(value / baseline_value - 1) * 100
```

Requirements:

* use a clearly identified baseline;
* support multiple series;
* handle missing baseline observations;
* avoid forward-filling by default;
* return the effective baseline date;
* never fabricate zero returns when a baseline is unavailable.

### E. Period return

Create a helper for calculating change over a defined number of observations or a date period.

It should support the project’s likely use cases such as:

* 21-session return;
* 3-month return;
* year-to-date return.

Do not create one overcomplicated function with many unrelated flags.

A small set of focused helpers is preferable.

### F. Latest and previous observations

Create reusable helpers for:

* latest valid observation per metric;
* previous valid observation per metric;
* previous distinct value where required;
* latest observation date per metric.

These may reuse existing Home logic if appropriate.

Avoid maintaining two competing implementations.

### G. Monthly market resampling

Create a reusable helper for converting daily market data to monthly observations.

Default behaviour should normally use the final valid observation of each month for price or index levels.

The function should:

* state the aggregation used;
* preserve metric identifiers;
* sort output correctly;
* not be used automatically for economic flow variables.

### H. Coverage checks

Create a small utility that can report:

* requested metrics present;
* requested metrics missing;
* first valid date per metric;
* latest valid date per metric;
* number of valid observations.

This will later support API validation and user-facing data notes.

---

## 2. Shared analytical Streamlit components

Inspect the current Home components before adding new abstractions.

Create or extend a shared component module for analytical pages.

A suitable location may be:

```text
src/api/dashboard/components/shared_components.py
```

and/or:

```text
src/api/dashboard/components/chart_components.py
```

Do not move Home-specific components unless there is a clear benefit and behaviour remains unchanged.

Implement only reusable presentation functions such as:

```python
inject_dashboard_styles()
render_analytical_page_header(...)
render_section_heading(...)
render_kpi_strip(...)
render_chart_panel_header(...)
render_page_summary(...)
render_chart_insight(...)
render_data_freshness_note(...)
render_methodology_note(...)
render_empty_state(...)
```

The exact function names may differ.

Requirements:

* components should receive prepared data;
* components should not query APIs;
* components should not perform economic calculations;
* escape dynamic HTML content where relevant;
* avoid large repeated inline CSS;
* keep functions reasonably small;
* preserve the Home page.

Do not implement final Plotly chart functions for every chart type yet unless a minimal wrapper is genuinely useful.

If a reusable chart wrapper is introduced, it should handle only presentation-level concerns such as:

* container width;
* consistent config;
* mode-bar settings;
* common margins;
* transparent background.

It should not decide economic transformations.

---

## 3. Shared analytical stylesheet

Create a shared external stylesheet for the analytical pages, for example:

```text
src/api/dashboard/styles/dashboard.css
```

Use the established Home design language as the reference.

Include reusable styles for:

* analytical page headers;
* section headings;
* KPI grids or strips;
* summary panels;
* chart containers;
* chart metadata;
* insight panels;
* source and methodology notes;
* empty states;
* responsive layouts.

Requirements:

* do not copy the entire Home stylesheet unnecessarily;
* do not redesign Home;
* use restrained borders and shadows;
* avoid gradients, excessive colour and animation;
* make two-column chart layouts collapse cleanly;
* avoid hard-coded widths that cause overflow;
* retain readable spacing on narrow screens.

---

## 4. Shared chart-display conventions

Where appropriate, introduce reusable Python constants or helper configuration for:

* Plotly display configuration;
* consistent margins;
* hover mode;
* responsive width;
* removal of unnecessary toolbar actions;
* default legend orientation;
* date-axis formatting.

Do not hard-code all series colours globally in this task unless the repository already has a colour system.

A later task may define page-specific semantic colours.

---

## 5. Tests

Add focused unit tests for transformation logic.

At minimum test:

### Date preparation

* unsorted dates become sorted;
* invalid dates are handled as documented;
* original input is not unexpectedly mutated.

### Normalisation

* two complete series rebase to 100;
* the first common valid date is used;
* missing early values are handled correctly;
* no common valid baseline is handled safely;
* zero baseline values do not cause silent invalid output.

### Cumulative returns

* correct return values;
* correct effective baseline;
* missing baseline handling.

### Latest observations

* latest valid value;
* previous valid value;
* previous distinct value;
* metrics with only one observation.

### Monthly resampling

* final valid daily observation is selected for each month;
* metrics remain separated;
* output is sorted.

### Coverage

* present and missing metrics are correctly identified;
* first and latest dates are correct.

Do not add brittle CSS tests.

---

## 6. Non-goals

Do not:

* complete Macro Pulse;
* create all remaining page files;
* redesign navigation;
* alter economic metric definitions;
* create new data sources;
* add LLM-generated commentary;
* perform broad unrelated refactoring;
* replace the FastAPI–Streamlit separation;
* start duplicate servers automatically.

---

## 7. Validation

After implementation:

1. Run the new targeted tests.
2. Run relevant existing tests.
3. Import the new component and utility modules to confirm no import errors.
4. Confirm the Home page still imports successfully.
5. Confirm no existing Home behaviour was intentionally changed.
6. Check whether Streamlit and Uvicorn were already running before starting anything.
7. Do not claim visual validation unless the rendered output was actually inspected.

## Final response

Summarise:

* files created or modified;
* helpers added;
* component abstractions added;
* styling added;
* tests run and results;
* existing logic reused;
* assumptions;
* anything deferred for the Macro Pulse implementation.
