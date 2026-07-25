# MacroUK Dashboard

MacroUK Dashboard is a public UK macroeconomic dashboard and portfolio project demonstrating Python ETL, API ingestion, economic data modelling, SQLite, FastAPI, Streamlit, Plotly, GitHub Actions and cloud deployment.

It combines official economic series with selected market-price proxies to present growth, inflation, labour markets, monetary policy, housing, equities, sterling, commodities and fixed income in one date-aware interface.

## Dashboard pages

- Home: six headline indicators and current economic highlights.
- Macro Pulse: GDP, inflation and labour-market momentum.
- Monetary Policy & Liquidity: Bank Rate, SONIA, money growth and business credit.
- Housing Market & Consumer Credit: mortgage rates, house prices, transactions and borrowing.
- Financial Markets & Equities: UK equity tiers, housebuilders and selected company proxies.
- Currency, Commodities & Fixed Income: sterling, ETF price proxies, gold and oil.

## Architecture

```text
External data sources
    ↓
Python ETL pipeline
    ↓
SQLite analytical warehouse
    ↓
S3-compatible object storage
    ↓
Streamlit local read-only copy
```

GitHub Actions runs the complete ETL pipeline, validates the warehouse and uploads only a successful `economic_warehouse.db`. Streamlit downloads that file once when required and queries its local copy through shared Python page services.

FastAPI remains as an optional portfolio/API interface. Its routes wrap the same page services, but FastAPI and Uvicorn are not required by the deployed Streamlit application.

## What I engineered vs what I delegated to AI

I designed and manually engineered the project's core architecture, including its purpose, source selection, ETL structure, SQLite warehouse, FastAPI architecture, configuration model, chart plan and initial dashboard implementation.

This established the system's structure and technical direction. I built the Home and Macro Pulse pages first, creating the patterns that AI later followed across the rest of the dashboard. The Home page already included the six headline KPIs, API flow and config-driven foundation; AI primarily expanded its presentation, interpretation and professional polish.

AI was then used to accelerate implementation within that architecture. It completed the remaining analytical pages using the existing Home and Macro Pulse implementations as guides, handled much of the chart presentation layer, introduced the service modules under `src/api`, and implemented the final deployment workflow covering pipeline hardening, warehouse validation, GitHub Actions, object storage and Streamlit deployment.

In practical terms, I defined and built the system; AI helped scale, refine and complete it.

## Data sources

- Office for National Statistics
- Bank of England
- HM Land Registry
- Yahoo Finance market data

Series update on different schedules and may be revised. ETF and company data are market-price proxies, not official yields or complete sector indices. The dashboard is descriptive and is not financial advice.

## Local development

Python 3.13 and the exact dependency versions in `requirements.txt` are used by the deployment workflow.

```bash
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Build, validate and run the dashboard:

```bash
python -m src.etl.pipeline_runner
python -m src.validation.validate_warehouse
python -m streamlit run src/api/dashboard/app.py
```

The dashboard reads SQLite directly and does not need a local API server.

Run tests:

```bash
python -m pytest -q
```

### Optional FastAPI interface

```bash
python -m uvicorn src.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the optional API documentation.

## Warehouse refresh workflow

The workflow at `.github/workflows/build-warehouse.yml` runs daily at 05:30 UTC, can be started manually with **Actions → Build and publish warehouse → Run workflow**, and also runs when ETL/configuration files change.

It performs these gated steps:

1. Restore the previous warehouse when one is available, enabling an incremental refresh.
2. Run `python -m src.etl.pipeline_runner`.
3. Run `python -m src.validation.validate_warehouse`.
4. Run the complete test suite.
5. Upload the database only after every prior step succeeds.

### Required GitHub Actions secrets

| Secret | Purpose |
|---|---|
| `OBJECT_STORAGE_ENDPOINT` | S3-compatible endpoint, such as an R2 or B2 endpoint |
| `OBJECT_STORAGE_ACCESS_KEY_ID` | Object-storage access key |
| `OBJECT_STORAGE_SECRET_ACCESS_KEY` | Object-storage secret |
| `OBJECT_STORAGE_BUCKET` | Destination bucket |
| `OBJECT_STORAGE_REGION` | S3 region; use the provider's required value |
| `OBJECT_STORAGE_DATABASE_KEY` | Optional stable object key; defaults to `economic_warehouse.db` |

The credentials require read/write access to that one bucket/object. Do not commit them to the repository.

## Streamlit deployment

The Streamlit Community Cloud entrypoint is:

```text
src/api/dashboard/app.py
```

Configure this Streamlit secret:

```toml
MACROUK_DATABASE_URL = "https://your-public-or-signed-download-url/economic_warehouse.db"
```

Equivalent environment variables are supported:

- `MACROUK_DATABASE_URL` — remote database URL, required when no usable local database exists.
- `MACROUK_DATABASE_PATH` — optional local path override.
- `MACROUK_FORCE_DATABASE_REFRESH` — optional `true`/`false` refresh override.

The database is downloaded to a temporary `.download` file, checked with SQLite `integrity_check`, and atomically moved into place. A valid local database is reused, and Streamlit caches path resolution for the process so the download is not repeated on widget reruns.

For Cloudflare R2 or another private S3 bucket, expose the database through a stable public/custom-domain URL or another long-lived HTTPS download URL. The S3 upload credentials belong only in GitHub Actions; Streamlit needs only the download URL.

## Publishing checklist

1. Create the S3-compatible bucket.
2. Add the GitHub Actions secrets listed above.
3. Run the warehouse workflow manually and confirm the uploaded object.
4. Configure a stable HTTPS download URL for the object.
5. Create the Streamlit Community Cloud app using `src/api/dashboard/app.py`.
6. Add `MACROUK_DATABASE_URL` to the app's secrets.
7. Deploy and verify all six pages.
8. Replace the public dashboard URL placeholder below.

Public dashboard: **https://your-streamlit-app-url.example**

Detailed analytical definitions remain in [`charts.md`](charts.md), and the optional API notes are in [`api.md`](api.md).
