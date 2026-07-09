"""Build derived calculation tables for the UK macro dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.etl.db_utils import get_connection
from src.utilities.config_loader import load_config


MACRO_CONFIG = load_config("calculations", "macro") or {}
HOUSING_DERIVED_CONFIG = load_config("calculations", "housing_derived") or {}
YAHOO_CONFIG = load_config("metric_manifest", "y_finance_metrics") or {}

DAILY_BOE_METRICS = ["BANK_RATE_DA", "SONIA"]
YAHOO_METRICS = list(YAHOO_CONFIG.keys())
SNAPSHOT_METRICS = [
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
    "LONDON_PRICE_PREMIUM",
    "CASH_BUYER_SHARE",
    "MORTGAGE_BUYER_SHARE",
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

STANDARD_CALC_COLUMNS = [
    "DATE",
    "METRIC_ID",
    "METRIC_NAME",
    "VALUE",
    "UNIT",
    "FREQUENCY",
    "CHANGE_TYPE",
    "PREVIOUS_VALUE",
    "CHANGE",
    "CHANGE_PCT",
    "CHANGE_PP",
    "ROLLING_3",
    "ROLLING_12",
    "ROLLING_4Q",
    "VALUE_YEAR_AGO",
    "YOY_CHANGE",
    "YOY_CHANGE_PCT",
    "YOY_CHANGE_PP",
    "TREND",
    "DISPLAY_CHANGE",
    "DISPLAY_YOY_CHANGE",
]

DAILY_BOE_COLUMNS = [
    "DATE",
    "METRIC_ID",
    "METRIC_NAME",
    "VALUE",
    "UNIT",
    "PREVIOUS_VALUE",
    "CHANGE",
    "CHANGE_PP",
    "ROLLING_7D",
    "ROLLING_30D",
    "VALUE_30D_AGO",
    "CHANGE_30D_PP",
    "VALUE_365D_AGO",
    "CHANGE_1Y_PP",
    "DISPLAY_CHANGE",
    "DISPLAY_30D_CHANGE",
    "DISPLAY_1Y_CHANGE",
]

MARKET_DAILY_COLUMNS = [
    "DATE",
    "METRIC_ID",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "ADJ_CLOSE",
    "VOLUME",
    "PRICE_FOR_RETURNS",
    "PREVIOUS_CLOSE",
    "RETURN_1D",
    "RETURN_5D",
    "RETURN_21D",
    "RETURN_63D",
    "RETURN_126D",
    "RETURN_252D",
    "RETURN_YTD",
    "MA_20",
    "MA_50",
    "MA_200",
    "ROLLING_52W_HIGH",
    "DRAWDOWN_52W",
    "ROLLING_VOL_30D",
]

MARKET_MONTHLY_COLUMNS = [
    "DATE",
    "MONTHLY_CLOSE",
    "MONTHLY_ADJ_CLOSE",
    "MONTHLY_PRICE_FOR_RETURNS",
    "MONTHLY_VOLUME",
    "METRIC_ID",
    "RETURN_1M",
    "RETURN_3M",
    "RETURN_6M",
    "RETURN_12M",
    "RETURN_YTD",
    "ROLLING_3M",
    "ROLLING_12M",
    "TREND",
]

SNAPSHOT_COLUMNS = [
    "METRIC_ID",
    "METRIC_NAME",
    "CATEGORY",
    "SOURCE_TABLE",
    "LATEST_DATE",
    "LATEST_VALUE",
    "UNIT",
    "DISPLAY_CHANGE",
    "DISPLAY_YOY_CHANGE",
    "TREND",
]

def _read_series(metric_ids: list[str], source: str | None = None) -> pd.DataFrame:
    if not metric_ids:
        return pd.DataFrame()

    placeholders = ", ".join(["?"] * len(metric_ids))
    params: list[str] = list(metric_ids)
    query = f"""
        SELECT date, metric_id, metric_name, value, unit, source, frequency
        FROM economic_series
        WHERE metric_id IN ({placeholders})
    """

    if source is not None:
        query += " AND source = ?"
        params.append(source)

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["date", "metric_id", "value"]).sort_values(["metric_id", "date"])


def _safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return (numerator / denominator - 1) * 100


def _add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["display_change"] = np.select(
        [
            df["change_type"].eq("pct"),
            df["change_type"].isin(["pp", "points", "flow"]),
        ],
        [
            df["change_pct"],
            df["change"],
        ],
        default=df["change"],
    )
    df["display_yoy_change"] = np.select(
        [
            df["change_type"].eq("pct"),
            df["change_type"].isin(["pp", "points", "flow"]),
        ],
        [
            df["yoy_change_pct"],
            df["yoy_change"],
        ],
        default=df["yoy_change"],
    )
    return df


def _standard_calculations(df: pd.DataFrame, config: dict, default_frequency: str = "Monthly") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=STANDARD_CALC_COLUMNS)

    frames = []

    for metric_id, metric_df in df.groupby("metric_id", sort=False):
        metric_df = metric_df.sort_values("date").copy()
        frequency = (metric_df["frequency"].dropna().iloc[-1] if metric_df["frequency"].notna().any() else default_frequency)
        frequency_label = str(frequency)
        is_quarterly = frequency_label.lower().startswith("q")

        out = metric_df[["date", "metric_id", "metric_name", "value", "unit", "frequency"]].copy()
        out["change_type"] = config.get(metric_id, {}).get("change_type", "pct")
        out["previous_value"] = out["value"].shift(1)
        out["change"] = out["value"] - out["previous_value"]
        out["change_pct"] = _safe_pct(out["value"], out["previous_value"])
        out["change_pp"] = out["change"]

        if is_quarterly:
            out["rolling_3"] = np.nan
            out["rolling_12"] = np.nan
            out["rolling_4q"] = out["value"].rolling(4, min_periods=4).mean()
            out["value_year_ago"] = out["value"].shift(4)
            trend_base = out["rolling_4q"]
        else:
            out["rolling_3"] = out["value"].rolling(3, min_periods=3).mean()
            out["rolling_12"] = out["value"].rolling(12, min_periods=12).mean()
            out["rolling_4q"] = np.nan
            out["value_year_ago"] = out["value"].shift(12)
            trend_base = out["rolling_12"]

        out["yoy_change"] = out["value"] - out["value_year_ago"]
        out["yoy_change_pct"] = _safe_pct(out["value"], out["value_year_ago"])
        out["yoy_change_pp"] = out["yoy_change"]

        if is_quarterly:
            trend_missing = trend_base.isna()
            trend_up = out["value"] > trend_base
            trend_down = out["value"] < trend_base
        else:
            trend_missing = out["rolling_3"].isna() | out["rolling_12"].isna()
            trend_up = out["rolling_3"] > out["rolling_12"]
            trend_down = out["rolling_3"] < out["rolling_12"]

        out["trend"] = np.select([trend_missing, trend_up, trend_down], [None, "Rising", "Falling"], default="Flat")
        frames.append(_add_display_columns(out))

    result = pd.concat(frames, ignore_index=True)
    return _uppercase_columns(result)


def _uppercase_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.upper() for col in df.columns]
    return df


def _validate_basic(df: pd.DataFrame, table_name: str) -> None:
    if df.empty:
        print(f"{table_name}: no rows to write.")
        return
    assert df["DATE"].notna().all(), f"{table_name} has null DATE values"
    assert df["METRIC_ID"].notna().all(), f"{table_name} has null METRIC_ID values"
    duplicates = df[df.duplicated(["DATE", "METRIC_ID"], keep=False)]
    assert duplicates.empty, f"{table_name} has duplicate DATE/METRIC_ID rows"


def _write_table(df: pd.DataFrame, table_name: str) -> None:
    _validate_basic(df, table_name)
    with get_connection() as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Built {table_name}: {len(df)} rows.")


def _resample_daily_boe_monthly() -> pd.DataFrame:
    df = _read_series(DAILY_BOE_METRICS, source="BOE")
    if df.empty:
        return pd.DataFrame()

    rows = []
    for metric_id, rule, output_id in [
        ("BANK_RATE_DA", "last", "BANK_RATE_DA_MONTHLY"),
        ("SONIA", "mean", "SONIA_MONTHLY_AVG"),
    ]:
        metric_df = df[df["metric_id"].eq(metric_id)].copy()
        if metric_df.empty:
            continue

        metric_df = metric_df.set_index("date").sort_index()
        values = metric_df["value"].resample("ME").last() if rule == "last" else metric_df["value"].resample("ME").mean()
        out = values.dropna().reset_index()
        out["metric_id"] = output_id
        out["metric_name"] = output_id.replace("_", " ").title()
        out["unit"] = "%"
        out["source"] = "BOE"
        out["frequency"] = "Monthly"
        out = out.rename(columns={"date": "date", "value": "value"})
        rows.append(out[["date", "metric_id", "metric_name", "value", "unit", "source", "frequency"]])

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_macro_calculations() -> pd.DataFrame:
    configured_metrics = [metric for metric in MACRO_CONFIG if metric not in {"BANK_RATE_DA_MONTHLY", "SONIA_MONTHLY_AVG"}]
    raw = _read_series(configured_metrics)
    monthly_boe = _resample_daily_boe_monthly()
    if not monthly_boe.empty:
        raw = pd.concat([raw, monthly_boe], ignore_index=True)
    df = _standard_calculations(raw, MACRO_CONFIG)
    _write_table(df, "macro_calculations")
    return df


def build_daily_boe_calculations() -> pd.DataFrame:
    raw = _read_series(DAILY_BOE_METRICS, source="BOE")
    if raw.empty:
        df = pd.DataFrame(columns=DAILY_BOE_COLUMNS)
        _write_table(df, "daily_boe_calculations")
        return df

    frames = []
    for _, metric_df in raw.groupby("metric_id", sort=False):
        out = metric_df[["date", "metric_id", "metric_name", "value", "unit"]].copy().sort_values("date")
        out["previous_value"] = out["value"].shift(1)
        out["change"] = out["value"] - out["previous_value"]
        out["change_pp"] = out["change"]
        out["rolling_7d"] = out["value"].rolling(7, min_periods=7).mean()
        out["rolling_30d"] = out["value"].rolling(30, min_periods=30).mean()
        out["value_30d_ago"] = out["value"].shift(30)
        out["change_30d_pp"] = out["value"] - out["value_30d_ago"]
        out["value_365d_ago"] = out["value"].shift(365)
        out["change_1y_pp"] = out["value"] - out["value_365d_ago"]
        out["display_change"] = out["change_pp"]
        out["display_30d_change"] = out["change_30d_pp"]
        out["display_1y_change"] = out["change_1y_pp"]
        frames.append(out)

    df = _uppercase_columns(pd.concat(frames, ignore_index=True))
    _write_table(df, "daily_boe_calculations")
    return df


def _read_market_wide() -> pd.DataFrame:
    raw = _read_series([f"{metric}_{field}" for metric in YAHOO_METRICS for field in ["open", "high", "low", "close", "adj close", "adj_close", "volume"]], source="YAHOO_FINANCE")
    if raw.empty:
        return pd.DataFrame()

    parts = []
    for metric_id in YAHOO_METRICS:
        prefix = f"{metric_id}_"
        metric_raw = raw[raw["metric_id"].str.startswith(prefix)].copy()
        if metric_raw.empty:
            continue
        metric_raw["field"] = metric_raw["metric_id"].str[len(prefix):].str.replace(" ", "_", regex=False).str.upper()
        wide = metric_raw.pivot_table(index="date", columns="field", values="value", aggfunc="mean").reset_index()
        wide["METRIC_ID"] = metric_id
        for field in ["OPEN", "HIGH", "LOW", "CLOSE", "ADJ_CLOSE", "VOLUME"]:
            if field not in wide.columns:
                wide[field] = np.nan
        parts.append(wide[["date", "METRIC_ID", "OPEN", "HIGH", "LOW", "CLOSE", "ADJ_CLOSE", "VOLUME"]])

    if not parts:
        return pd.DataFrame()

    df = pd.concat(parts, ignore_index=True).rename(columns={"date": "DATE"})
    return df.sort_values(["METRIC_ID", "DATE"])


def build_market_calculations_daily() -> pd.DataFrame:
    df = _read_market_wide()
    if df.empty:
        df = pd.DataFrame(columns=MARKET_DAILY_COLUMNS)
        _write_table(df, "market_calculations_daily")
        return df

    frames = []
    for _, metric_df in df.groupby("METRIC_ID", sort=False):
        out = metric_df.sort_values("DATE").copy()
        out["PRICE_FOR_RETURNS"] = out["ADJ_CLOSE"].fillna(out["CLOSE"])
        price = out["PRICE_FOR_RETURNS"]
        out["PREVIOUS_CLOSE"] = price.shift(1)
        for days in [1, 5, 21, 63, 126, 252]:
            out[f"RETURN_{days}D"] = _safe_pct(price, price.shift(days))
        out["YEAR"] = out["DATE"].dt.year
        first_price = out.groupby("YEAR")["PRICE_FOR_RETURNS"].transform("first")
        out["RETURN_YTD"] = _safe_pct(price, first_price)
        out["MA_20"] = price.rolling(20, min_periods=20).mean()
        out["MA_50"] = price.rolling(50, min_periods=50).mean()
        out["MA_200"] = price.rolling(200, min_periods=200).mean()
        out["ROLLING_52W_HIGH"] = price.rolling(252, min_periods=252).max()
        out["DRAWDOWN_52W"] = _safe_pct(price, out["ROLLING_52W_HIGH"])
        out["ROLLING_VOL_30D"] = price.pct_change().rolling(30, min_periods=30).std() * np.sqrt(252) * 100
        frames.append(out.drop(columns=["YEAR"]))

    result = pd.concat(frames, ignore_index=True)
    _write_table(result, "market_calculations_daily")
    return result


def build_market_calculations_monthly(daily_df: pd.DataFrame | None = None) -> pd.DataFrame:
    if daily_df is None or daily_df.empty:
        daily_df = build_market_calculations_daily()
    if daily_df.empty:
        daily_df = pd.DataFrame(columns=MARKET_MONTHLY_COLUMNS)
        _write_table(daily_df, "market_calculations_monthly")
        return daily_df

    frames = []
    for _, metric_df in daily_df.groupby("METRIC_ID", sort=False):
        metric_df = metric_df.sort_values("DATE").set_index("DATE")
        monthly = pd.DataFrame(
            {
                "MONTHLY_CLOSE": metric_df["CLOSE"].resample("ME").last(),
                "MONTHLY_ADJ_CLOSE": metric_df["ADJ_CLOSE"].resample("ME").last(),
                "MONTHLY_PRICE_FOR_RETURNS": metric_df["PRICE_FOR_RETURNS"].resample("ME").last(),
                "MONTHLY_VOLUME": metric_df["VOLUME"].resample("ME").sum(min_count=1),
            }
        ).dropna(subset=["MONTHLY_PRICE_FOR_RETURNS"])
        monthly["METRIC_ID"] = metric_df["METRIC_ID"].iloc[0]
        monthly = monthly.reset_index()
        price = monthly["MONTHLY_PRICE_FOR_RETURNS"]
        for months in [1, 3, 6, 12]:
            monthly[f"RETURN_{months}M"] = _safe_pct(price, price.shift(months))
        monthly["YEAR"] = monthly["DATE"].dt.year
        first_price = monthly.groupby("YEAR")["MONTHLY_PRICE_FOR_RETURNS"].transform("first")
        monthly["RETURN_YTD"] = _safe_pct(price, first_price)
        monthly["ROLLING_3M"] = price.rolling(3, min_periods=3).mean()
        monthly["ROLLING_12M"] = price.rolling(12, min_periods=12).mean()
        missing = monthly["ROLLING_3M"].isna() | monthly["ROLLING_12M"].isna()
        monthly["TREND"] = np.select(
            [missing, monthly["ROLLING_3M"] > monthly["ROLLING_12M"], monthly["ROLLING_3M"] < monthly["ROLLING_12M"]],
            [None, "Rising", "Falling"],
            default="Flat",
        )
        frames.append(monthly.drop(columns=["YEAR"]))

    result = pd.concat(frames, ignore_index=True)
    _write_table(result, "market_calculations_monthly")
    return result


def build_housing_derived_calculations() -> pd.DataFrame:
    required = [
        "UK_HPI_AVG_PRICE_LONDON",
        "UK_HPI_AVG_PRICE_UK",
        "UK_HPI_AVG_PRICE_NW",
        "UK_HPI_CASH_SALES_VOL",
        "UK_HPI_VOLUME_UK",
        "UK_HPI_MORTGAGE_SALES_VOL",
        "UK_HPI_FTB_AVG_PRICE",
        "UK_HPI_CASH_AVG_PRICE",
        "UK_HPI_MORTGAGE_AVG_PRICE",
    ]
    raw = _read_series(required)
    if raw.empty:
        df = pd.DataFrame(columns=STANDARD_CALC_COLUMNS)
        _write_table(df, "housing_derived_calculations")
        return df

    wide = raw.pivot_table(index="date", columns="metric_id", values="value", aggfunc="mean").sort_index()
    formulas = {
        "LONDON_PRICE_PREMIUM": wide.get("UK_HPI_AVG_PRICE_LONDON") / wide.get("UK_HPI_AVG_PRICE_UK"),
        "NW_PRICE_RATIO": wide.get("UK_HPI_AVG_PRICE_NW") / wide.get("UK_HPI_AVG_PRICE_UK"),
        "CASH_BUYER_SHARE": (wide.get("UK_HPI_CASH_SALES_VOL") / wide.get("UK_HPI_VOLUME_UK")) * 100,
        "MORTGAGE_BUYER_SHARE": (wide.get("UK_HPI_MORTGAGE_SALES_VOL") / wide.get("UK_HPI_VOLUME_UK")) * 100,
        "FTB_PRICE_RATIO": wide.get("UK_HPI_FTB_AVG_PRICE") / wide.get("UK_HPI_AVG_PRICE_UK"),
        "CASH_VS_MORTGAGE_PRICE_RATIO": wide.get("UK_HPI_CASH_AVG_PRICE") / wide.get("UK_HPI_MORTGAGE_AVG_PRICE"),
    }

    frames = []
    for metric_id, values in formulas.items():
        if values is None:
            continue
        out = values.dropna().reset_index(name="value")
        if out.empty:
            continue
        out["metric_id"] = metric_id
        out["metric_name"] = metric_id.replace("_", " ").title()
        out["unit"] = "%" if "SHARE" in metric_id else "ratio"
        out["frequency"] = "Monthly"
        frames.append(out[["date", "metric_id", "metric_name", "value", "unit", "frequency"]])

    derived = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    df = _standard_calculations(derived, HOUSING_DERIVED_CONFIG)
    _write_table(df, "housing_derived_calculations")
    return df


def build_dashboard_snapshot() -> pd.DataFrame:
    rows = []
    table_specs = [
        ("macro_calculations", "macro"),
        ("market_calculations_monthly", "markets"),
        ("housing_derived_calculations", "housing"),
    ]

    with get_connection() as conn:
        existing_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        for table_name, category in table_specs:
            if table_name not in existing_tables:
                continue
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            if df.empty:
                continue
            wanted = set(SNAPSHOT_METRICS)
            df = df[df["METRIC_ID"].isin(wanted)].copy()
            if df.empty:
                continue
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
            latest = df.sort_values("DATE").groupby("METRIC_ID", as_index=False).tail(1)
            for _, row in latest.iterrows():
                if table_name == "market_calculations_monthly":
                    latest_value = row.get("MONTHLY_PRICE_FOR_RETURNS")
                    display_change = row.get("RETURN_1M")
                    display_yoy_change = row.get("RETURN_12M")
                    unit = YAHOO_CONFIG.get(row["METRIC_ID"], {}).get("unit")
                    metric_name = YAHOO_CONFIG.get(row["METRIC_ID"], {}).get("name", row["METRIC_ID"])
                else:
                    latest_value = row.get("VALUE")
                    display_change = row.get("DISPLAY_CHANGE")
                    display_yoy_change = row.get("DISPLAY_YOY_CHANGE")
                    unit = row.get("UNIT")
                    metric_name = row.get("METRIC_NAME", row["METRIC_ID"])
                rows.append(
                    {
                        "METRIC_ID": row["METRIC_ID"],
                        "METRIC_NAME": metric_name,
                        "CATEGORY": category,
                        "SOURCE_TABLE": table_name,
                        "LATEST_DATE": row["DATE"].date().isoformat() if pd.notna(row["DATE"]) else None,
                        "LATEST_VALUE": latest_value,
                        "UNIT": unit,
                        "DISPLAY_CHANGE": display_change,
                        "DISPLAY_YOY_CHANGE": display_yoy_change,
                        "TREND": row.get("TREND"),
                    }
                )

    snapshot = pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS)
    if not snapshot.empty:
        snapshot = snapshot[snapshot["LATEST_VALUE"].notna()]
        assert not snapshot.duplicated(["METRIC_ID"]).any(), "dashboard_snapshot has duplicate METRIC_ID rows"
        assert snapshot["LATEST_DATE"].notna().all(), "dashboard_snapshot has null LATEST_DATE values"

    with get_connection() as conn:
        snapshot.to_sql("dashboard_snapshot", conn, if_exists="replace", index=False)
    print(f"Built dashboard_snapshot: {len(snapshot)} rows.")
    return snapshot


def main() -> None:
    macro_df = build_macro_calculations()
    build_daily_boe_calculations()
    market_daily_df = build_market_calculations_daily()
    build_market_calculations_monthly(market_daily_df)
    build_housing_derived_calculations()
    build_dashboard_snapshot()

    if not macro_df.empty:
        for metric_id, expected_change, expected_yoy in [
            ("CPI", "CHANGE_PP", "YOY_CHANGE_PP"),
            ("UK_HPI_AVG_PRICE_UK", "CHANGE_PCT", "YOY_CHANGE_PCT"),
            ("NET_LENDING_DWELLINGS_MO", "CHANGE", "YOY_CHANGE"),
        ]:
            subset = macro_df[macro_df["METRIC_ID"].eq(metric_id)].dropna(subset=["DISPLAY_CHANGE"])
            if not subset.empty:
                assert np.allclose(subset["DISPLAY_CHANGE"], subset[expected_change], equal_nan=True)
                assert np.allclose(subset["DISPLAY_YOY_CHANGE"], subset[expected_yoy], equal_nan=True)


if __name__ == "__main__":
    main()

# python -m src.etl.build_calculations
