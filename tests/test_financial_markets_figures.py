import unittest

from src.api.dashboard.components.chart_components import build_financial_markets_figure


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


if __name__ == "__main__":
    unittest.main()
