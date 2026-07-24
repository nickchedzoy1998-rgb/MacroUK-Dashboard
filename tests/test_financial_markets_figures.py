import unittest

from src.api.dashboard.components.chart_components import (
    DEFAULT_SECTOR_VIEW,
    SECTOR_VIEW_MODES,
    build_financial_markets_figure,
)


def chart(metric):
    return {
        "series_metadata": [{"metric": metric, "label": "FTSE 100", "unit": "Index", "role": "line", "axis": "left"}],
        "records": [{"date": "2026-07-09", "values": {metric: 99.0, "FTSE_100_close": 8000.0}}, {"date": "2026-07-10", "values": {metric: 100.0, "FTSE_100_close": 8100.0}}],
    }


class FinancialMarketsFigureTests(unittest.TestCase):
    def test_normalised_figure_has_one_trace_and_baseline(self):
        figure = build_financial_markets_figure(chart("FTSE_100_close_normalised"))
        self.assertEqual(len(figure.data), 1)
        self.assertTrue(any(shape.y0 == 100 for shape in figure.layout.shapes))
        self.assertIn("Original close", figure.data[0].hovertemplate)

    def test_sector_proxy_modes_preserve_traces_and_update_axes(self):
        metrics = [
            ("EQ_BARC_close_normalised", "Barclays (rebased)", [100.0, 110.0]),
            ("EQ_BP_close_normalised", "BP (rebased)", [100.0, 90.0]),
            ("EQ_RIO_close_normalised", "Rio Tinto (rebased)", [100.0, 125.0]),
            ("EQ_GSK_close_normalised", "GSK (rebased)", [100.0, 105.0]),
            ("SGE_L_close_normalised", "Sage (rebased)", [100.0, 50000.0]),
        ]
        payload = {
            "id": "FM3",
            "series_metadata": [
                {"metric": metric, "label": label, "unit": "Index", "role": "line", "axis": "left"}
                for metric, label, _ in metrics
            ],
            "records": [
                {
                    "date": date,
                    "values": {
                        **{metric: values[index] for metric, _, values in metrics},
                        **{metric.removesuffix("_normalised"): values[index] for metric, _, values in metrics},
                    },
                }
                for index, date in enumerate(("2020-01-01", "2026-01-01"))
            ],
        }

        default = build_financial_markets_figure(payload)
        self.assertEqual(DEFAULT_SECTOR_VIEW, "Comparable growth")
        self.assertEqual(len(default.data), len(metrics))
        self.assertIn("log return", default.layout.yaxis.title.text.lower())
        self.assertEqual(default.layout.yaxis.type, "linear")
        self.assertTrue(all("(rebased)" not in trace.name for trace in default.data))
        self.assertIn("Rebased level", default.data[0].hovertemplate)

        logarithmic = build_financial_markets_figure(payload, SECTOR_VIEW_MODES[1])
        self.assertEqual(logarithmic.layout.yaxis.type, "log")
        self.assertEqual(len(logarithmic.data), len(metrics))

        absolute = build_financial_markets_figure(payload, SECTOR_VIEW_MODES[2])
        self.assertEqual(absolute.layout.yaxis.type, "linear")
        self.assertTrue(any(shape.y0 == 100 for shape in absolute.layout.shapes))
        self.assertEqual(len(absolute.data), len(metrics))


if __name__ == "__main__":
    unittest.main()
