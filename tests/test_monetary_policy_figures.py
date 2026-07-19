import unittest

from src.api.dashboard.components.chart_components import build_business_credit_figure, build_money_supply_figure, build_policy_rates_figure


class MonetaryPolicyFigureTests(unittest.TestCase):
    def test_mp1_step_rate_and_price_panel(self):
        chart = {"series_metadata": [{"metric": "BANK_RATE_DA", "label": "Bank Rate", "unit": "%", "role": "line", "axis": "left"}, {"metric": "SONIA", "label": "SONIA", "unit": "%", "role": "line", "axis": "left"}, {"metric": "ETF_UK_GILT_close", "label": "UK gilt ETF price proxy", "unit": "GBP price", "role": "price_proxy", "axis": "right"}], "records": [{"date": "2024-01-01", "values": {"BANK_RATE_DA": 4.0, "SONIA": 3.9, "ETF_UK_GILT_close": 9.8}}]}
        figure = build_policy_rates_figure(chart)
        self.assertEqual(len(figure.data), 3)
        self.assertEqual(figure.data[0].line.shape, "hv")

    def test_mp2_zero_line_and_mp3_axes(self):
        money = {"series_metadata": [{"metric": "M4_GROWTH_MO", "label": "M4", "unit": "%", "role": "line", "axis": "left"}], "records": [{"date": "2024-01-31", "values": {"M4_GROWTH_MO": -1.0}}]}
        self.assertTrue(any(shape.y0 == 0 for shape in build_money_supply_figure(money).layout.shapes))
        credit = {"series_metadata": [{"metric": "CORP_OVERDRAFT_COST_MO", "label": "Cost", "unit": "%", "role": "line", "axis": "left"}, {"metric": "NET_LENDING_CORP_MO", "label": "Lending", "unit": "%", "role": "bar", "axis": "right"}], "records": [{"date": "2024-01-31", "values": {"CORP_OVERDRAFT_COST_MO": 5.0, "NET_LENDING_CORP_MO": -2.0}}]}
        figure = build_business_credit_figure(credit)
        self.assertEqual({trace.type for trace in figure.data}, {"bar", "scatter"})
        self.assertIsNotNone(figure.layout.yaxis)
        self.assertIsNotNone(figure.layout.yaxis2)


if __name__ == "__main__":
    unittest.main()
