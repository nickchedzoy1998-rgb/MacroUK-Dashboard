"""Typed, deterministic transformations used by analytical dashboard pages.

The functions in this module operate on long-format data by default. They
return copies and never fill missing observations implicitly. Duplicate rows
are handled explicitly by :func:`prepare_time_series`.
"""

from __future__ import annotations

from typing import Literal, Sequence

import pandas as pd


DuplicatePolicy = Literal["keep_last", "keep_first", "raise"]


def prepare_time_series(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str | None = "metric_id",
    duplicate_policy: DuplicatePolicy = "keep_last",
) -> pd.DataFrame:
    """Return a dated, sorted copy with invalid dates removed.

    Dates are parsed with ``errors='coerce'`` and rows with invalid dates are
    dropped. Duplicate observations are identified by date plus metric when a
    metric column is present, otherwise by date alone. ``keep_last`` is the
    conservative default for a prepared data table whose later row generally
    represents the latest correction. Use ``raise`` when duplicates are not
    acceptable for a particular calculation.
    """
    if date_column not in frame.columns:
        raise KeyError(f"Missing date column: {date_column}")
    if metric_column is not None and metric_column not in frame.columns:
        raise KeyError(f"Missing metric column: {metric_column}")
    if duplicate_policy not in {"keep_last", "keep_first", "raise"}:
        raise ValueError(f"Unsupported duplicate policy: {duplicate_policy}")

    prepared = frame.copy()
    prepared[date_column] = pd.to_datetime(prepared[date_column], errors="coerce")
    prepared = prepared.dropna(subset=[date_column])

    duplicate_columns = [date_column]
    if metric_column is not None:
        duplicate_columns.append(metric_column)
    duplicated = prepared.duplicated(subset=duplicate_columns, keep=False)
    if duplicated.any():
        if duplicate_policy == "raise":
            raise ValueError("Duplicate observations found for the same date and metric")
        prepared = prepared.drop_duplicates(
            subset=duplicate_columns,
            keep=duplicate_policy.replace("keep_", ""),
        )

    return prepared.sort_values(duplicate_columns).reset_index(drop=True)


def _valid_long_frame(
    frame: pd.DataFrame,
    *,
    date_column: str,
    metric_column: str,
    value_column: str,
    metrics: Sequence[str] | None,
) -> tuple[pd.DataFrame, list[str]]:
    prepared = prepare_time_series(
        frame,
        date_column=date_column,
        metric_column=metric_column,
    )
    if value_column not in prepared.columns:
        raise KeyError(f"Missing value column: {value_column}")

    prepared[value_column] = pd.to_numeric(prepared[value_column], errors="coerce")
    prepared = prepared.dropna(subset=[value_column])
    requested = list(metrics) if metrics is not None else list(prepared[metric_column].dropna().unique())
    return prepared[prepared[metric_column].isin(requested)].copy(), requested


def normalise_to_common_baseline(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[str] | None = None,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    """Rebase requested series to 100 at their first common valid date.

    The returned frame retains the original value and adds
    ``normalised_value``. An empty frame and ``None`` are returned when a
    requested metric is missing, no exact common date exists, or every common
    candidate has a zero baseline. No values are forward-filled.
    """
    prepared, requested = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=metrics,
    )
    empty = prepared.assign(normalised_value=pd.Series(dtype="float64"))
    if not requested or set(requested) != set(prepared[metric_column].unique()):
        return empty.iloc[0:0].copy(), None

    counts = prepared.groupby(date_column)[metric_column].nunique()
    candidate_dates = counts[counts == len(requested)].index.sort_values()
    baseline_date: pd.Timestamp | None = None
    baseline_values: pd.Series | None = None
    for candidate in candidate_dates:
        values = prepared.loc[prepared[date_column] == candidate].set_index(metric_column)[value_column]
        if values.reindex(requested).notna().all() and (values.reindex(requested) != 0).all():
            baseline_date = pd.Timestamp(candidate)
            baseline_values = values.reindex(requested)
            break

    if baseline_date is None or baseline_values is None:
        return empty.iloc[0:0].copy(), None

    result = prepared.copy()
    result["normalised_value"] = result.apply(
        lambda row: (row[value_column] / baseline_values[row[metric_column]]) * 100,
        axis=1,
    )
    result["baseline_date"] = baseline_date
    return result, baseline_date


def cumulative_percentage_return(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[str] | None = None,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
    baseline_date: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    """Calculate cumulative percentage returns from a common valid baseline.

    With no ``baseline_date``, the first common valid date is selected. With a
    requested date, only an exact valid observation on that date qualifies;
    missing baselines are returned as an empty result rather than filled.
    """
    if baseline_date is None:
        normalised, effective_date = normalise_to_common_baseline(
            frame,
            metrics=metrics,
            date_column=date_column,
            metric_column=metric_column,
            value_column=value_column,
        )
    else:
        requested_date = pd.to_datetime(baseline_date, errors="coerce")
        if pd.isna(requested_date):
            raise ValueError("baseline_date must be a valid date")
        prepared, requested = _valid_long_frame(
            frame,
            date_column=date_column,
            metric_column=metric_column,
            value_column=value_column,
            metrics=metrics,
        )
        baseline_rows = prepared[prepared[date_column] == requested_date]
        if not requested or set(requested) != set(baseline_rows[metric_column].unique()):
            return prepared.iloc[0:0].assign(return_pct=pd.Series(dtype="float64")), None
        baseline_values = baseline_rows.set_index(metric_column)[value_column].reindex(requested)
        if baseline_values.isna().any() or (baseline_values == 0).any():
            return prepared.iloc[0:0].assign(return_pct=pd.Series(dtype="float64")), None
        normalised = prepared.copy()
        normalised["normalised_value"] = normalised.apply(
            lambda row: (row[value_column] / baseline_values[row[metric_column]]) * 100,
            axis=1,
        )
        normalised["baseline_date"] = requested_date
        effective_date = pd.Timestamp(requested_date)

    if normalised.empty or effective_date is None:
        return normalised.assign(return_pct=pd.Series(dtype="float64")), effective_date
    result = normalised.copy()
    result["return_pct"] = result["normalised_value"] - 100
    return result, effective_date


def return_over_observations(
    frame: pd.DataFrame,
    observations: int,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Calculate a return against ``observations`` prior valid rows per metric."""
    if observations < 1:
        raise ValueError("observations must be at least 1")
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    result = prepared.copy()
    baseline = result.groupby(metric_column)[value_column].shift(observations)
    result["return_pct"] = ((result[value_column] / baseline) - 1) * 100
    result.loc[baseline.isna() | baseline.eq(0), "return_pct"] = pd.NA
    return result


def return_over_period(
    frame: pd.DataFrame,
    period: str | pd.DateOffset,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Calculate returns from the latest valid value on or before a date cutoff.

    The cutoff is calculated separately for each metric from that metric's
    latest observation. This intentionally uses an existing observation and
    never fabricates one through forward-filling.
    """
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    offset = pd.tseries.frequencies.to_offset(period)
    latest = latest_observations(
        prepared,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
    ).set_index(metric_column)
    baselines: list[dict[str, object]] = []
    for metric, latest_row in latest.iterrows():
        cutoff = latest_row[date_column] - offset
        candidates = prepared[
            (prepared[metric_column] == metric) & (prepared[date_column] <= cutoff)
        ]
        if candidates.empty:
            continue
        baseline = candidates.iloc[-1]
        if baseline[value_column] == 0:
            continue
        baselines.append(
            {
                metric_column: metric,
                "baseline_date": baseline[date_column],
                "baseline_value": baseline[value_column],
            }
        )

    if not baselines:
        return latest.reset_index().iloc[0:0].assign(return_pct=pd.Series(dtype="float64"))

    baseline_frame = pd.DataFrame(baselines)
    result = latest.reset_index().merge(baseline_frame, on=metric_column, how="inner")
    result["return_pct"] = ((result[value_column] / result["baseline_value"]) - 1) * 100
    return result


def latest_observations(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Return the latest valid row for each metric."""
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    return prepared.drop_duplicates(metric_column, keep="last").reset_index(drop=True)


def previous_observations(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Return the previous valid row for each metric with at least two rows."""
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    return prepared.groupby(metric_column, group_keys=False).tail(2).groupby(
        metric_column, group_keys=False
    ).head(1).reset_index(drop=True)


def previous_distinct_observations(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Return the latest row before the latest value changed for each metric."""
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    rows = []
    for metric, group in prepared.groupby(metric_column, sort=False):
        latest = group.iloc[-1]
        previous = group[group[value_column] != latest[value_column]]
        if not previous.empty:
            rows.append(previous.iloc[-1])
    return pd.DataFrame(rows, columns=prepared.columns).reset_index(drop=True)


def latest_observation_dates(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Return one latest valid date per metric."""
    latest = latest_observations(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
    )
    return latest[[metric_column, date_column]]


def resample_market_data_monthly(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> pd.DataFrame:
    """Resample daily market levels to month-end using the final valid value."""
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=None,
    )
    if prepared.empty:
        return prepared
    result = (
        prepared.groupby(
            [metric_column, pd.Grouper(key=date_column, freq="ME")],
            sort=True,
        )[value_column]
        .last()
        .reset_index()
    )
    return result.sort_values([metric_column, date_column]).reset_index(drop=True)


def coverage_report(
    frame: pd.DataFrame,
    requested_metrics: Sequence[str],
    *,
    date_column: str = "date",
    metric_column: str = "metric_id",
    value_column: str = "value",
) -> dict[str, object]:
    """Report presence, date coverage and valid observation counts."""
    prepared, _ = _valid_long_frame(
        frame,
        date_column=date_column,
        metric_column=metric_column,
        value_column=value_column,
        metrics=requested_metrics,
    )
    present = [metric for metric in requested_metrics if metric in set(prepared[metric_column])]
    first_dates = prepared.groupby(metric_column)[date_column].min().to_dict()
    latest_dates = prepared.groupby(metric_column)[date_column].max().to_dict()
    counts = prepared.groupby(metric_column)[value_column].count().to_dict()
    return {
        "requested_metrics": list(requested_metrics),
        "present_metrics": present,
        "missing_metrics": [metric for metric in requested_metrics if metric not in present],
        "first_valid_date": first_dates,
        "latest_valid_date": latest_dates,
        "valid_observations": counts,
    }
