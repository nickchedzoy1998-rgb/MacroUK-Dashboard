import unittest

from src.api.services.home_summary import (
    build_highlights,
    build_summary,
    describe_bank_rate,
    describe_ftse,
    describe_gdp,
    describe_inflation,
    describe_unemployment,
)


HOME_CONFIG = {
    "INFLATION": {"target": 2.0},
}


def kpi(kpi_id, value=None, delta=None):
    return {
        "kpi_id": kpi_id,
        "metric_id": kpi_id,
        "value": value,
        "delta": delta,
    }


class HomeSummaryServiceTests(unittest.TestCase):
    def test_gdp_contraction(self):
        self.assertEqual(describe_gdp(kpi("GDP_GROWTH", value=-0.2)), "contracting")

    def test_gdp_modest_growth(self):
        self.assertEqual(describe_gdp(kpi("GDP_GROWTH", value=0.3)), "growing modestly")

    def test_inflation_above_target(self):
        self.assertEqual(
            describe_inflation(kpi("INFLATION", value=3.2), HOME_CONFIG["INFLATION"]),
            "materially above target",
        )

    def test_inflation_close_to_target(self):
        self.assertEqual(
            describe_inflation(kpi("INFLATION", value=2.1), HOME_CONFIG["INFLATION"]),
            "close to target",
        )

    def test_unemployment_rising_and_falling(self):
        self.assertEqual(describe_unemployment(kpi("UNEMPLOYMENT", delta=0.2)), "rising")
        self.assertEqual(describe_unemployment(kpi("UNEMPLOYMENT", delta=-0.2)), "falling")

    def test_bank_rate_increase_and_reduction(self):
        self.assertEqual(
            describe_bank_rate(kpi("BANK_RATE", value=4.5, delta=0.25)),
            "increased and elevated",
        )
        self.assertEqual(
            describe_bank_rate(kpi("BANK_RATE", value=3.75, delta=-0.25)),
            "reduced",
        )

    def test_negative_and_positive_ftse_movement(self):
        self.assertEqual(describe_ftse(kpi("FTSE_250", delta=1.5)), "showing positive momentum")
        self.assertEqual(describe_ftse(kpi("FTSE_250", delta=-1.5)), "showing negative momentum")

    def test_highlight_ranking_and_maximum_of_three(self):
        kpis = [
            kpi("GDP_GROWTH", value=-0.4),
            kpi("INFLATION", value=3.4),
            kpi("UNEMPLOYMENT", value=4.8, delta=0.3),
            kpi("BANK_RATE", value=4.25, delta=0.25),
            kpi("HOUSE_PRICE_GROWTH", value=-1.2),
            kpi("FTSE_250", value=23000, delta=-4.0),
        ]

        highlights = build_highlights(kpis, HOME_CONFIG)

        self.assertEqual(len(highlights), 3)
        self.assertEqual(highlights[0].kpi_id, "GDP_GROWTH")
        self.assertIn("INFLATION", {highlight.kpi_id for highlight in highlights})

    def test_summary_generation_when_some_kpi_values_are_missing(self):
        summary = build_summary(
            [
                kpi("GDP_GROWTH", value=None),
                kpi("INFLATION", value=2.1),
                kpi("UNEMPLOYMENT", value=4.5, delta=None),
            ],
            HOME_CONFIG,
        )

        self.assertTrue(summary.headline)
        self.assertIn("Inflation", summary.body)


if __name__ == "__main__":
    unittest.main()
