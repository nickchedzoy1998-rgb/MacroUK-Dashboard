import unittest

from src.api.dashboard.components.chart_components import build_buyer_composition_figure, build_household_borrowing_figure, build_mortgage_housing_figure, build_regional_housing_figure


class HousingCreditFigureTests(unittest.TestCase):
    def test_hc1_dual_axis_and_hc2_normalised(self):
        chart = {"series_metadata": [{"metric": "MORTGAGE_2YR_75LTV_MO", "label": "Mortgage", "unit": "%", "axis": "left"}, {"metric": "UK_HPI_YOY_CHANGE_UK", "label": "House price", "unit": "%", "axis": "right"}], "records": [{"date": "2024-01-31", "values": {"MORTGAGE_2YR_75LTV_MO": 4, "UK_HPI_YOY_CHANGE_UK": 1}}]}
        fig = build_mortgage_housing_figure(chart); self.assertIsNotNone(fig.layout.yaxis2)
        regional = {"series_metadata": [{"metric": "UK_HPI_AVG_PRICE_UK_normalised", "label": "UK", "unit": "Index", "axis": "left"}], "records": [{"date": "2024-01-31", "values": {"UK_HPI_AVG_PRICE_UK_normalised": 100}}]}
        self.assertEqual(len(build_regional_housing_figure(regional).data), 1)

    def test_hc3_stack_and_hc4_zero(self):
        composition = {"series_metadata": [{"metric": "cash", "label": "Cash", "unit": "Transactions", "role": "bar"}, {"metric": "mortgage", "label": "Mortgage", "unit": "Transactions", "role": "bar"}, {"metric": "total", "label": "Total", "unit": "Transactions", "role": "line"}], "records": [{"date": "2024-01-31", "values": {"cash": 40, "mortgage": 60, "total": 100}}]}
        self.assertEqual(build_buyer_composition_figure(composition).layout.barmode, "stack")
        borrowing = {"series_metadata": [{"metric": "secured", "label": "Secured", "unit": "GBP millions", "role": "line"}], "records": [{"date": "2024-01-31", "values": {"secured": -20}}]}
        self.assertTrue(any(shape.y0 == 0 for shape in build_household_borrowing_figure(borrowing).layout.shapes))


if __name__ == "__main__": unittest.main()
