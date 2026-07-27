# MacroUK Dashboard

MacroUK Dashboard is an end-to-end UK economic data platform that ingests, models, and presents official macroeconomic data alongside selected financial-market indicators.

The project demonstrates Python ETL, API ingestion, SQLite data modelling, FastAPI, Streamlit, Plotly, GitHub Actions, automated testing, and cloud deployment.

[View the live dashboard](https://macrouk-dashboard-apc8kgaynxm7njzzaqrmob.streamlit.app/) · [View the GitHub repository](https://github.com/nickchedzoy1998-rgb/MacroUK-Dashboard)

## Overview

MacroUK Dashboard brings together data from the Office for National Statistics, Bank of England, HM Land Registry, and Yahoo Finance in a single date-aware interface.

It covers:

- Economic growth
- Inflation
- Labour markets
- Monetary policy
- Housing
- Consumer credit
- UK equities
- Sterling
- Commodities
- Fixed income

The project was built as a portfolio demonstration of an end-to-end analytics engineering workflow rather than as a standalone visualisation exercise.

It includes:

- External API ingestion
- Configurable Python ETL pipelines
- An analytical SQLite warehouse
- Reusable service-layer logic
- An optional FastAPI interface
- A multi-page Streamlit application
- Automated validation and testing
- Scheduled GitHub Actions refreshes
- Cloud-hosted warehouse distribution

## Dashboard Pages

### Home

A high-level view of the UK economy using six headline indicators, economic highlights, and navigation into the analytical sections.

### Macro Pulse

Tracks current momentum across:

- GDP growth
- Inflation
- Employment
- Unemployment
- Wage growth

### Monetary Policy & Liquidity

Covers:

- Bank Rate
- SONIA
- Money-supply growth
- Notes and coin
- Corporate borrowing costs
- Business lending

### Housing Market & Consumer Credit

Includes:

- Mortgage rates
- UK house-price growth
- Regional house prices
- Housing transactions
- Mortgage-financed and cash-financed sales
- Secured lending
- Consumer credit

### Financial Markets & Equities

Presents:

- UK equity-market tiers
- Selected sector and company proxies
- Housebuilder performance
- Market-level comparative trends

### Currency, Commodities & Fixed Income

Covers:

- Sterling exchange rates
- Gilt and fixed-income proxies
- Gold
- Oil
- Selected ETF price series

## Architecture

```text
External data sources
        ↓
Python ETL pipeline
        ↓
SQLite analytical warehouse
        ↓
Warehouse validation and automated tests
        ↓
S3-compatible object storage
        ↓
Streamlit local read-only SQLite copy
```

The deployed application does not run the ETL pipeline at startup. Instead:

1. GitHub Actions runs the full extraction and preparation pipeline.
2. The generated SQLite warehouse is validated.
3. The automated test suite runs.
4. The database is uploaded only when all previous stages succeed.
5. Streamlit downloads the latest valid warehouse.
6. The application queries a local read-only SQLite copy through shared Python services.

FastAPI remains available as an optional interface, but the deployed Streamlit application does not require FastAPI or Uvicorn to be running.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Data ingestion and transformation | Python, pandas, requests, yfinance, PyYAML |
| Data storage and modelling | SQLite, SQLAlchemy, configuration-driven metric definitions, chart-oriented analytical tables |
| Application layer | FastAPI, Pydantic, Streamlit, Plotly |
| Testing and deployment | pytest, GitHub Actions, Cloudflare R2, Streamlit Community Cloud |

## Data Sources

### Office for National Statistics

Used for official UK macroeconomic indicators, including:

- GDP
- CPI
- Core inflation
- Unemployment
- Employment
- Wage growth

### Bank of England

Used for:

- Bank Rate
- SONIA
- Money and liquidity indicators
- Mortgage rates
- Lending and credit series

### HM Land Registry

Used for:

- UK house-price indices
- Regional house prices
- Transaction and sales-volume data

### Yahoo Finance

Used for selected financial-market proxies, including:

- Equity indices
- Exchange rates
- ETFs
- Commodities
- Company and sector proxies

## Repository Structure

```text
MacroUK-Dashboard/
├── .github/
│   └── workflows/
│       └── build-warehouse.yml
├── configs/
│   ├── charts.yaml
│   ├── endpoints.yaml
│   ├── metric_manifest.yaml
│   └── settings.yaml
├── data/
├── src/
│   ├── analytics/
│   ├── api/
│   │   ├── dashboard/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── database/
│   ├── etl/
│   │   ├── fetch/
│   │   └── prepare_datasets/
│   ├── utilities/
│   └── validation/
├── tests/
├── api.md
├── charts.md
├── requirements.txt
└── README.md
```

## ETL Pipeline

Run the complete pipeline with:

```bash
python -m src.etl.pipeline_runner
```

The pipeline executes the following stages in sequence.

### Extraction

1. Office for National Statistics
2. Bank of England
3. Yahoo Finance
4. HM Land Registry

### Preparation

1. Home KPI preparation
2. Macro Pulse preparation
3. Monetary Policy preparation
4. Housing and Consumer Credit preparation
5. Financial Markets preparation
6. Global Flows preparation

Each required step is treated as a deployment dependency. If a stage fails:

- The pipeline raises an error
- Later stages do not continue
- The process exits with a non-zero status
- The warehouse is not published

## Warehouse Validation

Validate the generated database with:

```bash
python -m src.validation.validate_warehouse
```

The validator checks:

- That the database exists
- That the file is non-empty
- SQLite integrity
- The presence of required analytical tables
- Non-empty table contents
- The presence of core economic metrics
- Successful construction of all six page-level responses

This provides a final gate between data preparation and publication.

## Application Design

### Shared Service Layer

The project uses a framework-independent service layer shared by Streamlit and FastAPI.

```text
Streamlit pages ──→ Shared page services ──→ SQLite
FastAPI routes  ──→ Shared page services ──→ SQLite
```

This avoids duplicating SQL, transformations, or response-building logic between the two interfaces.

### Streamlit

Streamlit provides:

- Page navigation
- KPI rendering
- Chart rendering
- Summaries
- Analytical insights
- Methodology notes
- Data-status messaging

### FastAPI

FastAPI remains available as an optional interface for:

- API demonstration
- Local development
- Interactive documentation
- Future external integrations

It is not required by the deployed Streamlit application.

## Database Distribution

The live application reads from a local SQLite file rather than querying object storage for every chart.

At startup:

1. The configured remote warehouse URL is resolved.
2. The database is downloaded to a temporary file.
3. SQLite integrity is checked.
4. The temporary file atomically replaces the previous local copy.
5. The final database is opened in read-only mode.
6. The path is cached for the Streamlit process.

This keeps the dashboard fast and avoids repeated remote requests during normal interaction.

## Automated Warehouse Refresh

The workflow is defined in `.github/workflows/build-warehouse.yml`.

It runs:

- Daily at 05:30 UTC
- Manually through GitHub Actions
- When relevant ETL, validation, configuration, or dependency files change

The workflow performs:

1. Repository checkout
2. Python setup
3. Dependency installation
4. Restoration of the latest warehouse where available
5. Complete ETL execution
6. Warehouse validation
7. Automated testing
8. Object-storage configuration checks
9. Upload of the validated database

The database is uploaded only after the pipeline, validator, and test suite all succeed.

## Deployment

### Streamlit Community Cloud

The live application is deployed from `src/api/dashboard/app.py`.

[Open the production dashboard](https://macrouk-dashboard-apc8kgaynxm7njzzaqrmob.streamlit.app/)

### Object Storage

The validated SQLite warehouse is stored in Cloudflare R2 using an S3-compatible interface.

The Streamlit application downloads the latest warehouse through a stable HTTPS URL.

## Environment Configuration

### Streamlit Application

The deployed application uses:

```dotenv
MACROUK_DATABASE_URL="https://your-public-database-url/economic_warehouse.db"
```

Optional environment variables:

| Variable | Purpose |
| --- | --- |
| `MACROUK_DATABASE_PATH` | Overrides the local database path |
| `MACROUK_FORCE_DATABASE_REFRESH` | Forces replacement of an otherwise valid local copy |

`MACROUK_DATABASE_URL` defines the remote warehouse location.

### GitHub Actions

The warehouse workflow expects the following repository secrets:

| Secret | Purpose |
| --- | --- |
| `OBJECT_STORAGE_ENDPOINT` | S3-compatible object-storage endpoint |
| `OBJECT_STORAGE_ACCESS_KEY_ID` | Object-storage access key |
| `OBJECT_STORAGE_SECRET_ACCESS_KEY` | Object-storage secret |
| `OBJECT_STORAGE_BUCKET` | Destination bucket |
| `OBJECT_STORAGE_REGION` | Provider-compatible region |
| `OBJECT_STORAGE_DATABASE_KEY` | Stable object key for the SQLite warehouse |

The credentials are stored only in GitHub Actions secrets and are not committed to the repository.

## Local Development

### Requirements

- Python 3.13
- Packages listed in `requirements.txt`

### Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run the Complete Local Workflow

Build the warehouse:

```bash
python -m src.etl.pipeline_runner
```

Validate it:

```bash
python -m src.validation.validate_warehouse
```

Run the test suite:

```bash
python -m pytest -q
```

Start the Streamlit application:

```bash
python -m streamlit run src/api/dashboard/app.py
```

The dashboard reads SQLite directly and does not require a local API server.

### Optional FastAPI Interface

Start the API locally with:

```bash
python -m uvicorn src.api.main:app --reload
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

## Configuration Model

The project uses YAML configuration to separate analytical and presentation metadata from application code.

Configuration controls include:

- Metric definitions
- Source identifiers
- Public labels
- Chart composition
- Units
- Axis assignments
- Transformation rules
- Display order
- KPI metadata
- Endpoint configuration
- Database settings

This allows charts and KPIs to remain consistent across preparation, API, and presentation layers.

## Testing

The repository includes tests covering areas such as:

- ETL preparation
- Pipeline failure propagation
- Database validation
- Service-layer response construction
- FastAPI routes
- Chart transformations
- Figure generation
- Streamlit data loading
- Database downloading
- Read-only database access
- Page-level integration
- Public-label validation

Run all tests with:

```bash
python -m pytest -q
```

## What I Engineered vs. What I Delegated to AI

I designed and manually engineered the project's core architecture, including:

- Project purpose
- Source selection
- ETL structure
- SQLite warehouse
- FastAPI architecture
- Configuration model
- Chart plan
- Initial dashboard implementation

I built the Home and Macro Pulse pages first, establishing the technical and visual patterns used throughout the project.

The original implementation already included:

- The six headline KPIs
- The API flow
- The configuration-driven foundation
- The initial chart architecture
- The core data model

AI was then used as an implementation accelerator within that architecture. It helped:

- Complete the remaining analytical pages
- Expand the chart presentation layer
- Professionalise summaries and interpretation
- Introduce the shared service modules under `src/api`
- Harden the ETL runner
- Implement warehouse validation
- Create the GitHub Actions deployment workflow
- Connect object storage and Streamlit deployment

In practical terms, I defined and built the system architecture; AI helped scale, refine, and complete the implementation.

## Analytical Limitations

The dashboard is descriptive rather than predictive.

Important limitations include:

- Official series update on different schedules
- Historical observations may be revised
- Observation dates differ across monthly, quarterly, and daily indicators
- ETF data are price proxies rather than official yields
- Company series are selected proxies rather than complete sector indices
- Commodity and gold prices are denominated in US dollars
- Some housing measures use England-and-Wales geography rather than the whole UK
- Market prices may reflect factors beyond UK macroeconomic conditions

> [!IMPORTANT]
> The dashboard is not financial advice.

## Further Documentation

- `charts.md` contains detailed chart definitions.
- `api.md` contains notes about the optional FastAPI interface.

## Status

| Component | Status |
| --- | --- |
| Live Streamlit application | Complete |
| Automated warehouse refresh | Complete |
| Object-storage publication | Complete |
| Read-only SQLite runtime | Complete |
| Warehouse validation | Complete |
| Automated testing | Complete |
| Optional FastAPI interface | Complete |

[Open the live dashboard](https://macrouk-dashboard-apc8kgaynxm7njzzaqrmob.streamlit.app/)
