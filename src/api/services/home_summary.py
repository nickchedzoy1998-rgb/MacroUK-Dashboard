from dataclasses import dataclass
from typing import Any, Literal


Direction = Literal["positive", "negative", "neutral"]


@dataclass(frozen=True)
class SummaryNarrative:
    headline: str
    body: str


@dataclass(frozen=True)
class Highlight:
    kpi_id: str
    title: str
    text: str
    importance: int
    direction: Direction


def _get_kpi(kpis: list[Any], kpi_id: str) -> Any | None:
    for kpi in kpis:
        if _field(kpi, "kpi_id") == kpi_id:
            return kpi
    return None


def _field(kpi: Any, name: str, default: Any = None) -> Any:
    if isinstance(kpi, dict):
        return kpi.get(name, default)
    return getattr(kpi, name, default)


def _config(home_config: dict[str, Any], kpi_id: str) -> dict[str, Any]:
    return home_config.get(kpi_id, {})


def _fmt_pp(value: float) -> str:
    return f"{abs(value):.1f} percentage points"


def _fmt_percent(value: float) -> str:
    return f"{value:.1f}%"


def _target(config: dict[str, Any]) -> float | None:
    target = config.get("target")
    return None if target is None else float(target)


def describe_gdp(kpi: Any | None) -> str | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    value = float(_field(kpi, "value"))
    if value < 0:
        return "contracting"
    if value <= 0.1:
        return "broadly flat"
    if value <= 0.5:
        return "growing modestly"
    return "showing stronger growth"


def describe_inflation(kpi: Any | None, config: dict[str, Any]) -> str | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    target = _target(config)
    if target is None:
        return None

    gap = float(_field(kpi, "value")) - target
    if gap >= 1.0:
        return "materially above target"
    if gap >= 0.3:
        return "moderately above target"
    if gap >= -0.3:
        return "close to target"
    return "below target"


def describe_unemployment(kpi: Any | None) -> str | None:
    if kpi is None or _field(kpi, "delta") is None:
        return None

    delta = float(_field(kpi, "delta"))
    if delta > 0.05:
        return "rising"
    if delta < -0.05:
        return "falling"
    return "broadly unchanged"


def describe_bank_rate(kpi: Any | None) -> str | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    value = float(_field(kpi, "value"))
    delta = _field(kpi, "delta")

    if delta is None or float(delta) == 0:
        movement = "unchanged"
    elif float(delta) > 0:
        movement = "increased"
    else:
        movement = "reduced"

    if value >= 4.0:
        return f"{movement} and elevated"
    return movement


def describe_house_prices(kpi: Any | None) -> str | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    value = float(_field(kpi, "value"))
    if value < 0:
        return "declining"
    if value <= 1.0:
        return "broadly flat"
    if value <= 5.0:
        return "showing moderate growth"
    return "showing strong growth"


def describe_ftse(kpi: Any | None) -> str | None:
    if kpi is None or _field(kpi, "delta") is None:
        return None

    delta = float(_field(kpi, "delta"))
    if delta > 1.0:
        return "showing positive momentum"
    if delta < -1.0:
        return "showing negative momentum"
    return "broadly flat"


def build_summary(kpis: list[Any], home_config: dict[str, Any]) -> SummaryNarrative:
    gdp = describe_gdp(_get_kpi(kpis, "GDP_GROWTH"))
    inflation = describe_inflation(
        _get_kpi(kpis, "INFLATION"),
        _config(home_config, "INFLATION"),
    )
    unemployment = describe_unemployment(_get_kpi(kpis, "UNEMPLOYMENT"))
    bank_rate = describe_bank_rate(_get_kpi(kpis, "BANK_RATE"))
    house_prices = describe_house_prices(_get_kpi(kpis, "HOUSE_PRICE_GROWTH"))
    ftse = describe_ftse(_get_kpi(kpis, "FTSE_250"))

    headline_parts = []
    if gdp:
        headline_parts.append("growth remains subdued" if gdp in {"broadly flat", "growing modestly"} else f"the economy is {gdp}")
    if inflation:
        headline_parts.append(f"inflation is {inflation}")

    headline = "UK indicators point to mixed economic conditions"
    if headline_parts:
        headline = " as ".join([headline_parts[0], headline_parts[1]]) if len(headline_parts) > 1 else headline_parts[0]
        headline = headline[0].upper() + headline[1:]

    body_sentences = []
    if gdp and inflation:
        body_sentences.append(
            f"The UK economy is {gdp}, while inflation is {inflation}."
        )
    elif gdp:
        body_sentences.append(f"The UK economy is {gdp}.")
    elif inflation:
        body_sentences.append(f"Inflation is {inflation}.")

    secondary_signals = []
    if unemployment:
        secondary_signals.append(f"unemployment is {unemployment}")
    if bank_rate:
        secondary_signals.append(f"Bank Rate is {bank_rate}")
    if house_prices:
        secondary_signals.append(f"house prices are {house_prices}")
    if ftse:
        secondary_signals.append(f"the FTSE 250 is {ftse}")

    if secondary_signals:
        body_sentences.append(
            f"Other headline signals show that {_join_phrases(secondary_signals)}."
        )

    body = " ".join(body_sentences) or (
        "Current headline indicators are available, but there is not enough "
        "complete KPI data to generate a fuller narrative."
    )

    return SummaryNarrative(headline=headline, body=body)


def _join_phrases(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def build_highlights(kpis: list[Any], home_config: dict[str, Any]) -> list[Highlight]:
    candidates = [
        _inflation_highlight(_get_kpi(kpis, "INFLATION"), _config(home_config, "INFLATION")),
        _gdp_highlight(_get_kpi(kpis, "GDP_GROWTH")),
        _bank_rate_highlight(_get_kpi(kpis, "BANK_RATE")),
        _unemployment_highlight(_get_kpi(kpis, "UNEMPLOYMENT")),
        _house_price_highlight(_get_kpi(kpis, "HOUSE_PRICE_GROWTH")),
        _ftse_highlight(_get_kpi(kpis, "FTSE_250")),
    ]
    highlights = [candidate for candidate in candidates if candidate is not None]
    highlights.sort(key=lambda item: item.importance, reverse=True)
    return highlights[:3]


def build_home_interpretation(
    kpis: list[Any],
    home_config: dict[str, Any],
) -> tuple[SummaryNarrative, list[Highlight]]:
    return build_summary(kpis, home_config), build_highlights(kpis, home_config)


def _inflation_highlight(kpi: Any | None, config: dict[str, Any]) -> Highlight | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    target = _target(config)
    if target is None:
        return None

    value = float(_field(kpi, "value"))
    gap = value - target
    if abs(gap) < 0.3:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Inflation is close to target",
            text=f"Consumer prices are rising at {_fmt_percent(value)}, close to the {_fmt_percent(target)} target.",
            importance=3,
            direction="neutral",
        )

    direction: Direction = "negative" if gap > 0 else "positive"
    title = "Inflation remains above target" if gap > 0 else "Inflation is below target"
    importance = 9 if abs(gap) >= 1.0 else 6
    relation = "faster than" if gap > 0 else "slower than"
    return Highlight(
        kpi_id=_field(kpi, "kpi_id"),
        title=title,
        text=f"Consumer prices are rising {_fmt_pp(gap)} {relation} the {_fmt_percent(target)} target.",
        importance=importance,
        direction=direction,
    )


def _gdp_highlight(kpi: Any | None) -> Highlight | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    value = float(_field(kpi, "value"))
    if value < 0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Output contracted",
            text=f"GDP fell by {_fmt_percent(abs(value))} compared with the previous quarter.",
            importance=10,
            direction="negative",
        )
    if value > 0.5:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Growth strengthened",
            text=f"GDP rose by {_fmt_percent(value)} compared with the previous quarter.",
            importance=7,
            direction="positive",
        )
    if value > 0.1:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Growth remains modest",
            text=f"GDP increased by {_fmt_percent(value)} compared with the previous quarter.",
            importance=4,
            direction="neutral",
        )
    return None


def _unemployment_highlight(kpi: Any | None) -> Highlight | None:
    if kpi is None or _field(kpi, "delta") is None:
        return None

    delta = float(_field(kpi, "delta"))
    if delta > 0.05:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Unemployment edged higher",
            text=f"The unemployment rate rose by {_fmt_pp(delta)} from the previous observation.",
            importance=7 if abs(delta) >= 0.2 else 5,
            direction="negative",
        )
    if delta < -0.05:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Unemployment edged lower",
            text=f"The unemployment rate fell by {_fmt_pp(delta)} from the previous observation.",
            importance=6 if abs(delta) >= 0.2 else 4,
            direction="positive",
        )
    return None


def _bank_rate_highlight(kpi: Any | None) -> Highlight | None:
    if kpi is None or _field(kpi, "delta") is None:
        return None

    delta = float(_field(kpi, "delta"))
    if delta > 0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Bank Rate increased",
            text=f"The policy rate rose by {_fmt_pp(delta)} at the latest distinct rate change.",
            importance=8,
            direction="negative",
        )
    if delta < 0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="Bank Rate was reduced",
            text=f"The policy rate fell by {_fmt_pp(delta)} at the latest distinct rate change.",
            importance=8,
            direction="positive",
        )
    return None


def _house_price_highlight(kpi: Any | None) -> Highlight | None:
    if kpi is None or _field(kpi, "value") is None:
        return None

    value = float(_field(kpi, "value"))
    if value < 0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="House prices are falling",
            text=f"Average UK house prices are down {_fmt_percent(abs(value))} over the year.",
            importance=7,
            direction="negative",
        )
    if value >= 5.0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="House-price growth is strong",
            text=f"Average UK house prices are up {_fmt_percent(value)} over the year.",
            importance=6,
            direction="positive",
        )
    if value > 1.0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="House prices are growing",
            text=f"Average UK house prices are up {_fmt_percent(value)} over the year.",
            importance=3,
            direction="neutral",
        )
    return None


def _ftse_highlight(kpi: Any | None) -> Highlight | None:
    if kpi is None or _field(kpi, "delta") is None:
        return None

    delta = float(_field(kpi, "delta"))
    if delta > 1.0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="FTSE 250 momentum is positive",
            text=f"The FTSE 250 rose {_fmt_percent(delta)} over the latest 21-session window.",
            importance=7 if delta >= 3.0 else 5,
            direction="positive",
        )
    if delta < -1.0:
        return Highlight(
            kpi_id=_field(kpi, "kpi_id"),
            title="FTSE 250 momentum is negative",
            text=f"The FTSE 250 fell {_fmt_percent(abs(delta))} over the latest 21-session window.",
            importance=7 if abs(delta) >= 3.0 else 5,
            direction="negative",
        )
    return Highlight(
        kpi_id=_field(kpi, "kpi_id"),
        title="FTSE 250 is broadly flat",
        text="The FTSE 250 changed little over the latest 21-session window.",
        importance=2,
        direction="neutral",
    )
