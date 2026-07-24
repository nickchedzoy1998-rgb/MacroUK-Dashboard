import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from src.api.dashboard.components.chart_components import (
    CHART_PALETTE,
    SERIES_STYLES,
    build_growth_momentum_figure,
    build_inflation_figure,
    build_labour_market_figure,
    resolve_series_style,
    resolve_series_styles,
)
from src.api.dashboard.components.shared_components import render_kpi_strip, render_section_heading
from src.api.services.macro_pulse_api import build_macro_pulse_response
from src.api.services.financial_markets_api import build_financial_markets_response
from src.api.services.global_flows_api import build_global_flows_response
from src.api.services.housing_credit_api import build_housing_credit_response
from src.api.services.monetary_policy_api import build_monetary_policy_response
from src.etl.prepare_datasets.macro_pulse import DB_PATH
from src.utilities.config_loader import load_config, resolve_metric_label


ROOT = Path(__file__).resolve().parents[1]
RAW_IDS = {
    "GDP_QOQ",
    "GDP_YOY",
    "UNRATE",
    "EMPRATE",
    "WAGE_GROWTH",
    "M4_GROWTH_MO",
    "NOTES_COINS_GROWTH_MO",
    "CORP_OVERDRAFT_COST_MO",
    "NET_LENDING_CORP_MO",
}
MOJIBAKE = ("Ã¢", "Ã", "Â", "â€™", "â€“", "â€œ", "â€", "�")


class LaunchPolishTests(unittest.TestCase):
    def test_kpi_strip_is_compact_balanced_html(self):
        kpis = [{
            "name": "Inflation rate",
            "value": 2.1,
            "delta": 0.1,
            "main_unit": "%",
            "delta_unit": "pp",
            "description": "Annual consumer-price growth.",
            "date": "2026-06-30",
        }]
        with patch("src.api.dashboard.components.shared_components.st.markdown") as markdown:
            render_kpi_strip(kpis)
        html = markdown.call_args.args[0]
        self.assertNotIn("\n", html)
        self.assertEqual(html.count("<div"), html.count("</div>"))
        self.assertEqual(html.count("<article"), html.count("</article>"))
        self.assertEqual(html.count("<section"), html.count("</section>"))
        self.assertFalse(any(line.strip() == "</div>" for line in html.splitlines()))

    def test_section_heading_cannot_create_a_markdown_closing_tag_artifact(self):
        with patch("src.api.dashboard.components.shared_components.st.markdown") as markdown:
            render_section_heading("Headline indicators")
        html = markdown.call_args.args[0]
        self.assertNotIn("\n", html)
        self.assertEqual(
            html,
            '<div class="dashboard-section-heading"><h2>Headline indicators</h2></div>',
        )

    def test_style_resolution_is_deterministic_and_distinct(self):
        self.assertEqual(resolve_series_style("BANK_RATE_DA"), resolve_series_style("BANK_RATE_DA"))
        self.assertEqual(resolve_series_style("BANK_RATE_DA")["shape"], "hv")
        self.assertEqual(resolve_series_style("CPI")["shape"], "spline")
        self.assertGreater(resolve_series_style("CPI")["smoothing"], 0)
        unknown = [f"UNKNOWN_METRIC_{index}" for index in range(len(CHART_PALETTE))]
        first = resolve_series_styles(unknown)
        second = resolve_series_styles(unknown)
        self.assertEqual(first, second)
        self.assertEqual(len({style["color"] for style in first.values()}), len(CHART_PALETTE))
        self.assertEqual(SERIES_STYLES["BANK_RATE_DA"]["color"], "#2f6690")

    def test_public_config_labels_do_not_expose_known_raw_ids(self):
        config = load_config("charts")
        for section_name in ("MacroPulse", "MonetaryPolicy", "HousingCredit", "FinancialMarkets", "GlobalFlows"):
            for chart in config[section_name].values():
                labels = chart.get("metric_labels", {})
                metrics = list(chart.get("metrics", [])) + list(chart.get("optional_metrics", []))
                for metric in metrics:
                    label = resolve_metric_label(metric, labels)
                    if label == metric:
                        self.assertIn(metric, {"SONIA"})
                    self.assertNotIn(label, RAW_IDS)

    def test_sparse_annual_gdp_trace_spans_full_prepared_coverage(self):
        with sqlite3.connect(DB_PATH) as conn:
            response = build_macro_pulse_response(conn)
        growth = response.charts[0].model_dump(mode="json")
        figure = build_growth_momentum_figure(growth)
        annual = next(trace for trace in figure.data if trace.name == "Annual GDP growth")
        self.assertGreaterEqual(len(annual.x), 70)
        self.assertLess(str(annual.x[0])[:4], "1960")
        self.assertGreaterEqual(str(annual.x[-1])[:4], "2024")
        self.assertFalse(any(value is None for value in annual.y))

    def test_api_public_labels_and_narratives_hide_internal_metric_ids(self):
        with sqlite3.connect(DB_PATH) as conn:
            responses = [
                build_macro_pulse_response(conn),
                build_monetary_policy_response(conn),
                build_housing_credit_response(conn),
                build_financial_markets_response(conn),
                build_global_flows_response(conn),
            ]
        config = load_config("charts")
        internal_ids = {
            metric
            for section_name in ("MacroPulse", "MonetaryPolicy", "HousingCredit", "FinancialMarkets", "GlobalFlows")
            for chart in config[section_name].values()
            for metric in [*chart.get("metrics", []), *chart.get("optional_metrics", [])]
            if "_" in metric
        }
        for response in responses:
            for chart in response.charts:
                for item in chart.series_metadata:
                    if item.label == item.metric:
                        self.assertIn(item.metric, {"SONIA"})
                public_text = " ".join(
                    filter(
                        None,
                        [
                            chart.title,
                            chart.description,
                            chart.insight.headline if chart.insight else None,
                            chart.insight.body if chart.insight else None,
                        ],
                    )
                )
                for metric in internal_ids:
                    self.assertNotIn(metric, public_text)
            response_text = f"{response.summary.headline} {response.summary.body}"
            for metric in internal_ids:
                self.assertNotIn(metric, response_text)

    def test_eligible_continuous_lines_are_smoothed_and_distinct(self):
        chart = {
            "series_metadata": [
                {"metric": "CPI", "label": "Headline CPI inflation", "unit": "%"},
                {"metric": "CORE_CPI", "label": "Core CPI inflation", "unit": "%"},
                {"metric": "HOUSE_PRICE_GROWTH", "label": "Housing-cost inflation", "unit": "%"},
            ],
            "records": [{
                "date": "2026-01-31",
                "values": {"CPI": 3.0, "CORE_CPI": 3.4, "HOUSE_PRICE_GROWTH": 2.5},
            }],
            "target": 2.0,
        }
        figure = build_inflation_figure(chart)
        self.assertEqual(len({trace.line.color for trace in figure.data}), 3)
        self.assertTrue(all(trace.line.shape == "spline" for trace in figure.data))

    def test_charts_default_to_five_years_and_controls_have_clear_space(self):
        chart = {
            "series_metadata": [
                {"metric": "CPI", "label": "Headline CPI inflation", "unit": "%"},
            ],
            "records": [
                {"date": "2010-01-31", "values": {"CPI": 3.0}},
                {"date": "2026-01-31", "values": {"CPI": 2.5}},
            ],
        }
        figure = build_inflation_figure(chart)
        self.assertEqual(str(figure.layout.xaxis.range[0])[:10], "2021-01-31")
        self.assertEqual(str(figure.layout.xaxis.range[1])[:10], "2026-01-31")
        self.assertEqual(figure.layout.xaxis.rangeselector.y, -0.20)
        self.assertEqual(figure.layout.xaxis.rangeselector.bgcolor, "rgba(255,255,255,0.98)")
        self.assertGreaterEqual(figure.layout.margin.b, 80)

        labour = {
            "series_metadata": [
                {"metric": "UNRATE", "label": "Unemployment rate", "unit": "%"},
                {"metric": "WAGE_GROWTH", "label": "Wage growth", "unit": "%"},
            ],
            "records": [
                {"date": "2010-01-31", "values": {"UNRATE": 5.0, "WAGE_GROWTH": 2.0}},
                {"date": "2026-01-31", "values": {"UNRATE": 4.5, "WAGE_GROWTH": 4.0}},
            ],
        }
        labour_figure = build_labour_market_figure(labour)
        self.assertFalse(labour_figure.layout.xaxis.rangeselector.buttons)
        self.assertTrue(labour_figure.layout.xaxis2.rangeselector.buttons)

    def test_source_and_config_are_free_of_known_mojibake(self):
        paths = [
            *ROOT.joinpath("src").rglob("*.py"),
            *ROOT.joinpath("src").rglob("*.css"),
            *ROOT.joinpath("configs").rglob("*.yaml"),
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for sequence in MOJIBAKE:
                self.assertNotIn(sequence, text, f"{sequence!r} found in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    unittest.main()
