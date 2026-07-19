# MacroUK Dashboard

MacroUK Dashboard is a descriptive UK macroeconomic dashboard. It combines official economic series with selected market-price proxies to support a clear, date-aware view of growth, inflation, labour markets, policy transmission, housing, equities, sterling, commodities and fixed income.

## Pages

- Home: headline indicators and dashboard navigation.
- Macro Pulse: growth, inflation and labour-market momentum.
- Monetary Policy & Liquidity: Bank Rate, SONIA, money growth and business credit.
- Housing Market & Consumer Credit: mortgage rates, house prices, transactions and borrowing.
- Financial Markets & Equities: UK equity tiers, housebuilders and selected company proxies.
- Currency, Commodities & Fixed Income: sterling, ETF price proxies, gold and oil.

## Architecture

The ETL layer writes source data and reproducible chart-oriented tables to SQLite. FastAPI assembles validated page responses from those prepared tables. Streamlit provides the page orchestration and Plotly rendering. Shared chart transformations and dashboard components live under `src/analytics` and `src/api/dashboard/components`.

Detailed analytical requirements and chart definitions are documented in [`charts.md`](charts.md).

## Local setup

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The configured SQLite warehouse is expected under `data/`. Source ingestion and preparation depend on the configured data sources and credentials where applicable.

## Run

Prepare the analytical tables after source data is available:

```powershell
venv\Scripts\python.exe -m src.etl.prepare_datasets.macro_pulse
venv\Scripts\python.exe -m src.etl.prepare_datasets.monetary_policy
venv\Scripts\python.exe -m src.etl.prepare_datasets.housing_credit
venv\Scripts\python.exe -m src.etl.prepare_datasets.financial_markets
venv\Scripts\python.exe -m src.etl.prepare_datasets.global_flows
```

Start the API and dashboard in separate terminals:

```powershell
venv\Scripts\python.exe -m uvicorn src.api.main:app --reload
venv\Scripts\python.exe -m streamlit run src/api/dashboard/app.py
```

Run tests with:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## Known limitations

Observation dates and release frequencies differ between indicators, and official series may be revised. ETF and company series are price proxies, not official yields or complete sector indices. Commodity prices and gold are USD-denominated. Housing transaction components use England-and-Wales geography where stated and are not interchangeable with UK-wide totals. Analysis is descriptive and is not financial advice.
