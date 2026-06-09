# API Guide for Pipeline Expansion

Since you are already down the rabbit hole with the ONS and Bank of England data structures, executing pulls for HM Land Registry and HM Treasury will feel familiar, though they require targeting different endpoints and handling varying structures.

Here is a straight-to-the-point technical guide on how to programmatically pull the rest of your data components.

## 1. HM Land Registry (`hmlr_metrics`)

Land Registry data is exposed via a dedicated SPARQL / Linked Data API. Because it uses structured semantic URIs, you do not need a complex query builder. You can hit a clean, standard HTTP GET JSON endpoint.

### Endpoint Structure

`GET https://landregistry.data.gov.uk/app/ukhpi/doc/by-context/months/{YEAR}-{MONTH}/regions/{REGION}/data.json`

### Python Implementation Pattern

Iterate through your config file, format the URL string dynamically with the lowercase string provided in your region keys, and extract the matching value from your field definitions:

```python
import requests

def fetch_hmlr_metric(year, month, region, field):
    # e.g., year="2026", month="04", region="greater-london"
    url = f"https://landregistry.data.gov.uk/app/ukhpi/doc/by-context/months/{year}-{month}/regions/{region}/data.json"

    response = requests.get(url)
    if response.status_code == 200:
        payload = response.json()
        # The result data is contained within a nested "result" wrapper
        data_item = payload.get("result", {}).get("items", [{}])[0]
        return data_item.get(field)
    return None
```

## 2. HM Treasury: Independent Forecasts (`hmt_metrics`)

The consensus metrics are published as a regular collection on GOV.UK. Because HMT does not expose a clean REST API for this specific compilation, you have two options for your ingestion script.

### Method A: GOV.UK Content API (Programmatic JSON Pathway)

GOV.UK maintains a systemic JSON mirror for all document pages. You can scan the underlying publication files without building brittle HTML scrapers.

`GET https://www.gov.uk/api/content/government/collections/forecasts-for-the-uk-economy`

Inside the JSON, look for `details["documents"]`.

Steps:

1. Extract the newest published document URL path, for example `/government/publications/forecasts-for-the-uk-economy-may-2026`.
2. Append `.json` to that publication page URL.
3. Download the attached `.csv` or `.xlsx` asset link found inside the payload.
4. Parse the median averages straight into your dashboard.

## 3. HM Treasury: Public Sector Finances (`hmt_metrics`)

Your config specifies `PUBLIC_SECTOR_NET_BORROWING`, `PUBLIC_SECTOR_NET_DEBT_PCT`, and `CGNCR_OUTTURN` as part of the Treasury group. Mechanically, these are co-managed and published straight through the ONS time-series asset database using the `publicsectorfinances` dataset.

### Endpoint Structure

`GET https://api.ons.gov.uk/timeseries/{CDID}/dataset/publicsectorfinances/data`

### Python Implementation Pattern

You can recycle your existing ONS API engine logic for this block. Just update the hardcoded dataset parameter context from `mm23` or `lms` to use your configured `ons_dataset` parameter:

```python
import requests

def fetch_hmt_ons_metric(cdid, dataset="publicsectorfinances"):
    # Cleans leading hyphens if they persist in older manual config instances
    clean_cdid = cdid.replace("-", "").lower()
    url = f"https://api.ons.gov.uk/timeseries/{clean_cdid}/dataset/{dataset}/data"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Extract the latest entry from the monthly time-series array
        latest_observation = data.get("months", [])[-1]
        return {
            "date": latest_observation.get("date"),
            "value": float(latest_observation.get("value"))
        }
    return None
```

## 4. DMO Gilt Remit, Auctions, & Threshold Parameters

The DMO annual issuance targets, tax thresholds, and PESA outturns are slow-moving structural variables (updating either weekly, quarterly, or annually post-Budget statement).

### Storage and Access Execution

Instead of building a real-time retrieval wrapper for endpoints that only update once a year (like your `FISCAL_THRESHOLD` elements or the `REMIT` split structures), the production-standard approach is to build a basic seed configuration migration file inside your application layer:

- Create a `seed_data.yaml` or a dedicated database table matching your config dictionary keys.
- Manually input or overwrite the values once during every major fiscal statement event.

### Weekly DMO Metric

For the `DMO_AUCTION_COVER_RATIO` metric, which is high-frequency/weekly, point an HTML parser script directly at the DMO Auction Results Summary Table:

`https://www.dmo.gov.uk/data/gilt-auctions/results-summary/`

Pull down the rolling average column payload from the published table and store it in your application layer.

## General Notes

- Keep each source isolated in its own ETL module.
- Reuse your config loader and normalization patterns wherever possible.
- Validate each metric before writing to SQLite.
- For slow-moving fiscal variables, prefer seed data or manual update flows instead of constant polling.
