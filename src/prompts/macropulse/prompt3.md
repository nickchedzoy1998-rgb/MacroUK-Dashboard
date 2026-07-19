# Prompt 3 — Implement the Macro Pulse FastAPI Contract

Read `charts.md` in full before making changes.

The shared analytical foundation and Macro Pulse prepared datasets should already exist.

This task is limited to implementing the FastAPI service, schemas and endpoint contract required by the Macro Pulse Streamlit page.

Do not build the final Streamlit page in this change.

## Objective

Create a clear, validated API response that provides all data needed to render the professional Macro Pulse page without requiring substantial economic transformation in Streamlit.

The API should expose:

* page metadata;
* page-level deterministic summary;
* headline KPIs;
* the three Macro Pulse chart datasets;
* chart metadata;
* chart-specific deterministic insights;
* coverage and freshness metadata.

---

## Before changing code

Inspect:

* existing API routers;
* current chart endpoints;
* `build_chart_endpoint`;
* current Pydantic conventions;
* Home response schemas;
* Macro Pulse prepared tables;
* existing service modules;
* current tests;
* existing route paths consumed by `macro_pulse.py`.

Preserve existing working routes where practical.

Do not create duplicate routes that expose the same information in incompatible formats without a clear migration plan.

---

## 1. Choose the API shape

Prefer a page-level endpoint unless the existing architecture strongly favours separate chart endpoints.

A recommended response shape is:

```python
{
    "page": {
        "id": "macro_pulse",
        "title": "Macro Pulse",
        "description": "Track UK growth, inflation and labour-market momentum."
    },
    "summary": {
        "headline": "...",
        "body": "..."
    },
    "kpis": [...],
    "charts": [
        {
            "id": "EGM",
            "title": "Economic Growth Momentum",
            "description": "Compare quarterly growth with the annual trend.",
            "frequency": "quarterly",
            "chart_type": "bar_line",
            "series_metadata": [...],
            "records": [...],
            "insight": {...},
            "coverage": {...}
        }
    ]
}
```

The precise structure may be adapted to repository conventions.

Requirements:

* stable field names;
* explicit chart IDs;
* deterministic ordering;
* ISO dates;
* no raw SQLite-specific field leakage;
* no need for Streamlit to infer units from metric names;
* Pydantic validation throughout.

---

## 2. Pydantic schemas

Create project-appropriate schemas for the equivalent of:

```python
MacroPulsePageMetadata
MacroPulseSummary
MacroPulseKPI
ChartSeriesMetadata
ChartCoverage
ChartInsight
MacroPulseChart
MacroPulseResponse
```

Avoid unnecessary inheritance complexity.

### KPI schema

Each KPI should include the fields already established by Home where relevant:

```text
id
metric
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

Reuse an existing shared KPI schema if one exists and fits.

### Series metadata

Each series should expose enough information for Streamlit to render it intentionally:

```text
metric
label
unit
role
axis
display_order
```

Possible `role` values might include:

* bar;
* line;
* reference.

Possible `axis` values:

* left;
* right.

Do not make Streamlit guess that GDP_QOQ is the bar series from its name.

### Chart records

Use a consistent representation.

For example, a wide-format growth record may be:

```python
{
    "date": "2026-03-31",
    "GDP_QOQ": 0.3,
    "GDP_YOY": 1.2
}
```

A long format is also acceptable if it fits the project better.

Choose one format intentionally and document it through schemas.

### Coverage schema

Expose:

* requested metrics;
* available metrics;
* missing metrics;
* first observation per metric;
* latest observation per metric;
* valid observation count.

Do not expose internal diagnostic structures directly if they are not stable.

---

## 3. Endpoint behaviour

Implement a route consistent with the project’s existing API style.

A possible route is:

```text
/api/macro-pulse/summary
```

or:

```text
/api/dashboard/macro-pulse
```

Do not rename existing route families casually.

The endpoint should:

1. load the prepared data;
2. load stable chart metadata from config;
3. obtain deterministic summaries and insights from the appropriate service;
4. serialize data through Pydantic;
5. return charts in configured order.

Do not query raw external sources.

Do not calculate major transformations inside the route function.

Keep the router thin.

---

## 4. Error and partial-data behaviour

Define explicit behaviour for:

### Required data missing

If a required prepared dataset is entirely unavailable:

* return an appropriate server error;
* log a useful diagnostic;
* do not expose a stack trace in the JSON response.

### One optional series missing

For example, a housing-cost inflation series may be unavailable.

In that case:

* return the chart with available required series;
* list the optional series under `missing_metrics`;
* do not fail the entire page.

### One chart unavailable

Prefer returning the rest of the page where architecture permits.

Possible approaches:

* include the chart with an empty record list and coverage metadata;
* or omit it and expose a page warning.

Choose one consistent approach.

The later Streamlit page must be able to distinguish:

* an API failure;
* an empty chart;
* a missing optional series.

### Missing summary or insight

The absence of optional commentary must not prevent chart data from being returned.

---

## 5. Chart-specific API requirements

### Economic Growth Momentum

Return:

* quarterly records;
* GDP_QOQ bar metadata;
* GDP_YOY line metadata;
* percentage units;
* zero-reference metadata if the chart system uses it;
* latest growth insight;
* coverage.

### Inflation Pressures

Return:

* monthly CPI;
* monthly core CPI;
* optional verified housing-related inflation;
* 2% target metadata;
* percentage units;
* latest insight;
* coverage and missing optional metrics.

Do not return house-price growth as housing inflation unless the metric was explicitly verified and renamed accurately.

### Labour Market Health

Return:

* unemployment rate;
* employment rate;
* wage growth;
* explicit axis or panel recommendations through metadata if needed;
* latest insight;
* coverage.

The API should not force all three series onto one visual axis.

---

## 6. Tests

Add focused API and service tests.

At minimum test:

### Successful response

* HTTP success;
* expected page ID;
* three chart IDs in correct order;
* required KPI fields;
* ISO dates;
* summary fields;
* valid Pydantic serialization.

### Growth chart

* quarterly records;
* correct series roles;
* percentage units;
* negative values preserved.

### Inflation chart

* target metadata present;
* optional missing metric represented correctly;
* CPI and core CPI returned.

### Labour chart

* all available series represented;
* axis or panel metadata present where required;
* partial monthly coverage serialized correctly.

### Partial data

* one optional series missing;
* one insight absent;
* one chart with no records;
* page response remains valid where intended.

### Failure

* missing required prepared table or service failure;
* concise API error;
* no stack trace exposed.

Reuse test fixtures where practical.

Do not depend on the live running server for unit tests.

---

## 7. Compatibility

The current Streamlit Macro Pulse page may still call older per-chart endpoints.

Do not leave the application in an unnecessarily broken intermediate state.

Use one of these approaches:

1. preserve old routes temporarily while adding the new page-level route;
2. update a shared endpoint builder without yet changing the page;
3. clearly document that the next prompt must update the consumer immediately.

Prefer temporary compatibility where it is simple.

Do not maintain duplicate route systems indefinitely.

---

## 8. Non-goals

Do not:

* render Plotly charts;
* add CSS;
* complete Streamlit layout;
* alter Home;
* add unrelated navigation;
* add external data;
* implement other analytical pages;
* put visual presentation logic into the API.

---

## 9. Validation

After implementation:

1. Run targeted API tests.
2. Run the relevant preparation process if fixtures require it.
3. Inspect the endpoint using the existing running Uvicorn process where possible.
4. Check whether Uvicorn is already running before starting another instance.
5. Confirm the returned JSON against the Pydantic schema.
6. Confirm chart ordering.
7. Confirm dates and nulls serialize correctly.
8. Confirm optional missing metrics do not fail the response.
9. Report whether the live endpoint was actually called.
10. Do not claim Streamlit validation in this task.

## Final response

Summarise:

* endpoint added or changed;
* schemas added;
* response structure;
* compatibility decisions;
* partial-data behaviour;
* tests and results;
* live endpoint validation performed;
* assumptions;
* anything the Streamlit implementation must know.
