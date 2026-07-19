# Prompt 4 — Build the Professional Macro Pulse Streamlit Page

Read `charts.md` in full before making changes.

The shared analytical components and styles, Macro Pulse prepared data, and Macro Pulse FastAPI endpoint should already exist.

This task is to complete the Macro Pulse Streamlit page as the reference implementation for all later analytical pages.

Do not implement any other analytical page in this change.

## Objective

Replace the current Macro Pulse API-debug scaffold with a polished analytical page that matches the professionalism of Home.

The page should allow a user to understand:

* current UK growth momentum;
* current inflation pressure;
* current labour-market conditions;
* how those signals have changed over time.

It must consume the FastAPI response rather than query SQLite directly.

---

## Before changing code

Inspect:

* `charts.md`;
* the completed Home page;
* Home components and CSS;
* shared analytical components;
* shared dashboard CSS;
* the Macro Pulse API schema and live JSON;
* current `macro_pulse.py`;
* Streamlit navigation conventions;
* charting library already used;
* whether Streamlit and Uvicorn are already running.

Use the API contract as the source of truth.

Do not reimplement economic calculations in Streamlit.

---

## 1. Remove the current debug behaviour

The existing Macro Pulse page currently prints API JSON.

Replace debug output such as:

```python
st.write(data)
```

with proper rendering.

Remove obsolete loops or endpoint calls that no longer fit the final API contract.

Retain useful logging, but do not expose raw response data to the user.

---

## 2. API request and validation

Create a clear fetch function with:

* a sensible timeout;
* handling for request exceptions;
* HTTP status validation;
* JSON decoding validation;
* top-level response-shape validation.

The page should distinguish:

* API unavailable;
* invalid API response;
* valid page response with one empty chart;
* optional commentary missing.

Required behaviour:

* if the entire API response is unavailable or invalid, show a concise error and stop;
* if one chart contains no records, show a chart-level empty state and continue rendering the rest;
* if optional summary or insight data is missing, hide that section cleanly;
* do not expose exceptions or stack traces.

Use shared API helpers if the repository already contains them.

Avoid creating another nearly identical request utility.

---

## 3. Page structure

Use this order:

```text
Page header

Headline indicators

Macro Pulse overview panel

Economic Growth Momentum

Inflation Pressures

Labour Market Health

Methodology and data note
```

The page should feel like a professional analytical product, not a notebook.

---

## 4. Page header

Render:

### Title

```text
Macro Pulse
```

### Description

Use a concise description such as:

```text
Track the UK economy through growth, inflation and labour-market momentum.
```

Use the shared analytical page-header component.

Do not use a large marketing hero.

---

## 5. KPI strip

Render the API-provided page KPIs in a responsive strip or grid.

Requirements:

* three or four cards;
* equal heights;
* clear latest value;
* optional delta;
* concise description;
* observation date;
* correct delta-direction semantics;
* consistent formatting with Home.

Reuse shared KPI components.

Do not copy Home card code into `macro_pulse.py`.

If one KPI is unavailable:

* show `Not available` if the API intentionally provides the card;
* or omit it if the API contract omits unavailable KPIs;
* keep the layout stable.

---

## 6. Macro Pulse overview

Render the API-provided deterministic page summary below the KPI strip.

The panel should include:

* small label such as `Current assessment`;
* summary headline;
* one or two sentence body.

Use restrained styling consistent with the Home summary panel.

Do not generate or modify the summary in Streamlit.

If no summary is returned, omit the panel without leaving awkward blank space.

---

## 7. Chart 1 — Economic Growth Momentum

### Visual type

* GDP_QOQ as bars;
* GDP_YOY as a line;
* quarterly x-axis.

Use API series metadata rather than hard-coding metric roles where practical.

### Requirements

* include a visible zero line;
* preserve negative bars;
* use percentage formatting;
* show quarter and values in the hover tooltip;
* clearly label both series;
* keep legend placement consistent;
* avoid a second y-axis unless genuinely necessary, since both series use percentage units;
* use a full-width chart panel unless a two-column layout remains clearly readable.

### Chart panel copy

Title:

```text
Economic Growth Momentum
```

Subtitle:

```text
Compare short-term quarterly growth with the broader annual trend.
```

Use API metadata where available.

### Insight

Render the chart-specific deterministic insight below or beside the chart.

Do not infer new claims from the plotted data in Streamlit.

### Empty state

If records are empty:

* show a professional chart-level empty state;
* still render the rest of the page.

---

## 8. Chart 2 — Inflation Pressures

### Visual type

Multi-line monthly chart.

Expected series:

* headline CPI;
* core CPI;
* optional verified housing-related inflation series.

### Requirements

* include a labelled 2% target reference line;
* format y-axis as percentages;
* use consistent series labels;
* clearly show missing optional series through a compact note, not an error;
* do not show house-price growth as housing-cost inflation;
* hover should show month and each available series;
* avoid excessive point markers.

### Chart panel copy

Title:

```text
Inflation Pressures
```

Subtitle:

```text
Track headline and underlying price growth against the inflation target.
```

### Insight

Render the API-provided inflation insight.

If the optional housing-related series is missing, a short coverage note may say:

```text
A separate housing-cost inflation series is not currently available in this dataset.
```

Use API coverage metadata where possible.

Do not hard-code this message if the metric later becomes available.

---

## 9. Chart 3 — Labour Market Health

The three labour series represent different concepts.

Do not force them onto one axis merely because they are percentages.

Choose the clearest implementation supported by the API metadata.

Preferred options:

### Option A: Coordinated panel

One chart panel containing:

* unemployment and employment rates together;
* wage growth in a smaller aligned chart below.

This is the preferred default if it remains visually clear.

### Option B: Carefully labelled dual-axis chart

Use only if the shared chart system supports it clearly.

Requirements:

* unemployment and employment rates must remain distinguishable;
* wage growth must have an explicit axis;
* axis labels should match series colours;
* no implication that equal vertical positions mean equal economic magnitude.

### Chart panel copy

Title:

```text
Labour Market Health
```

Subtitle:

```text
Assess employment conditions alongside the pace of wage growth.
```

### Insight

Render the API-provided labour insight.

Mixed signals should be styled neutrally rather than forced into an improving or worsening category.

---

## 10. Chart styling

Use the existing charting library and shared conventions.

All three charts should share:

* transparent or page-matched background;
* consistent font sizing;
* restrained gridlines;
* consistent margins;
* responsive width;
* readable hover labels;
* unified legend styling;
* no unnecessary range slider;
* no 3D effects;
* no unnecessary toolbar buttons.

Do not use a different visual theme for each chart.

Use a restrained and consistent series palette.

Where the same series appears elsewhere later, its colour should be reusable through metadata or shared constants.

Do not introduce a large colour-system refactor unless needed.

---

## 11. Layout

Use full-width chart panels by default.

A two-column layout may be used only if:

* both charts remain readable;
* legends and date axes do not become cramped;
* the mobile layout collapses cleanly.

A reasonable first version is:

```text
Growth — full width

Inflation — full width

Labour — full width
```

Professionalism is more important than fitting more above the fold.

---

## 12. Data freshness and methodology

At the bottom of the page, add a concise note covering:

* GDP updates quarterly;
* inflation and labour indicators update monthly;
* observation dates may differ between series;
* charts use the latest available prepared data;
* analysis is descriptive rather than financial advice.

Use the shared methodology component.

Do not add a long essay.

Where useful, each chart should also show:

* latest observation date;
* coverage start date;
* missing optional series.

Keep metadata visually secondary.

---

## 13. Navigation

Ensure the page can be reached using the existing Streamlit navigation.

Do not update all Home navigation cards in this task unless Macro Pulse’s existing navigation is broken.

Do not create links to unfinished pages.

A simple route back to Home is acceptable if it matches current app navigation conventions.

---

## 14. Code organisation

Keep `macro_pulse.py` as an orchestration layer.

It should primarily:

1. inject styles;
2. fetch and validate the API response;
3. render the header;
4. render KPIs;
5. render summary;
6. pass chart records and metadata into rendering helpers;
7. render methodology notes.

Move reusable chart construction or rendering functions into the shared chart component module.

Possible functions include:

```python
build_growth_momentum_figure(...)
build_inflation_figure(...)
build_labour_market_figure(...)
render_chart_panel(...)
```

Page-specific figure builders may live in a Macro Pulse component module if they are not reusable elsewhere.

Do not put all HTML, API logic and chart construction into one large page file.

---

## 15. Tests

Add targeted tests where practical.

At minimum test:

### Response validation

* valid response accepted;
* missing required top-level fields rejected;
* optional summary absent;
* chart records empty.

### Figure builders

* expected trace count;
* GDP bars and line use correct trace types;
* zero reference exists;
* inflation target line exists;
* optional inflation series omitted safely;
* labour implementation uses intended axes or coordinated panels;
* dates sorted.

Do not assert pixel-level appearance.

If Streamlit component functions are difficult to unit test, test the pure figure-building functions and data validation separately.

---

## 16. Live validation

The app and Uvicorn may already be running.

Before starting a process:

* check whether the required service is already active;
* reuse it where possible;
* do not start duplicate instances on the same port;
* do not terminate unrelated Python processes.

Validate:

1. the Macro Pulse endpoint returns successfully;
2. the Streamlit page loads;
3. raw JSON is no longer displayed;
4. KPI cards render;
5. summary renders;
6. all available charts render;
7. the optional missing inflation series is handled cleanly;
8. chart insights render;
9. empty-state behaviour works;
10. the layout remains usable at a narrower width;
11. Home still works;
12. Macro Pulse navigation still works.

Do not claim visual validation unless the rendered page was actually inspected.

---

## 17. Non-goals

Do not:

* implement Monetary Policy;
* implement Housing;
* implement market pages;
* redesign Home;
* add forecasting;
* add an economic calendar;
* add AI commentary;
* add downloads unless trivial and explicitly justified;
* add complex user filters beyond what the current data supports;
* refactor unrelated ETL code.

---

## Final response

Summarise:

* page files and shared components modified;
* charts implemented;
* layout decisions;
* error and empty-state handling;
* tests and results;
* whether the live API and Streamlit page were inspected;
* whether existing running processes were reused;
* assumptions;
* anything that should become a shared pattern for the next four pages.
