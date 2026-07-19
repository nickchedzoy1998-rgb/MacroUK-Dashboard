import unittest

from src.api.dashboard.components.chart_components import (
    build_growth_momentum_figure,
    build_inflation_figure,
    build_labour_market_figure,
)


def chart_payload():
    return {
        "series_metadata": [
            {"metric": "GDP_QOQ", "label": "Quarterly GDP", "unit": "%", "role": "bar", "axis": "left"},
            {"metric": "GDP_YOY", "label": "Annual GDP", "unit": "%", "role": "line", "axis": "left"},
        ],
        "records": [
            {"date": "2024-06-30", "values": {"GDP_QOQ": -0.2, "GDP_YOY": None}},
            {"date": "2024-03-31", "values": {"GDP_QOQ": 0.1, "GDP_YOY": 1.2}},
        ],
        "zero_reference": 0.0,
    }


class MacroPulseFigureTests(unittest.TestCase):
    def test_growth_has_bar_line_and_zero_reference(self):
        figure = build_growth_momentum_figure(chart_payload())
        self.assertEqual([trace.type for trace in figure.data], ["bar", "scatter"])
        self.assertTrue(any(shape.type == "line" and shape.y0 == 0 for shape in figure.layout.shapes))
        self.assertEqual(str(list(figure.data[0].x)[0])[:10], "2024-03-31")

    def test_inflation_target_and_optional_series_are_safe(self):
        chart = {
            "series_metadata": [
                {"metric": "CPI", "label": "CPI", "unit": "%", "role": "line", "axis": "left"},
                {"metric": "CORE_CPI", "label": "Core CPI", "unit": "%", "role": "line", "axis": "left"},
                {"metric": "HOUSE_PRICE_GROWTH", "label": "Housing cost inflation", "unit": "%", "role": "line", "axis": "left", "optional": True},
            ],
            "records": [{"date": "2024-01-31", "values": {"CPI": 3.0, "CORE_CPI": 4.0, "HOUSE_PRICE_GROWTH": None}}],
            "target": 2.0,
        }
        figure = build_inflation_figure(chart)
        self.assertEqual(len(figure.data), 2)
        self.assertTrue(any(shape.type == "line" and shape.y0 == 2 for shape in figure.layout.shapes))

    def test_labour_figure_uses_coordinated_panels(self):
        chart = {
            "series_metadata": [
                {"metric": "UNRATE", "label": "Unemployment", "unit": "%", "role": "line", "axis": "left"},
                {"metric": "EMPRATE", "label": "Employment", "unit": "%", "role": "line", "axis": "left"},
                {"metric": "WAGE_GROWTH", "label": "Wage growth", "unit": "%", "role": "line", "axis": "right"},
            ],
            "records": [{"date": "2024-01-31", "values": {"UNRATE": 4.5, "EMPRATE": 74.0, "WAGE_GROWTH": 5.0}}],
        }
        figure = build_labour_market_figure(chart)
        self.assertEqual(len(figure.data), 3)
        self.assertEqual(len(figure.layout.annotations), 2)


if __name__ == "__main__":
    unittest.main()
