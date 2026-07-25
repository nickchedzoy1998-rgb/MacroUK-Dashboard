from src.utilities.build_url import build_chart_endpoint


def test_build_chart_endpoint_uses_registered_api_prefixes() -> None:
    assert build_chart_endpoint("FinancialMarkets", "summary") == "http://127.0.0.1:8000/api/financial-markets/summary"
    assert build_chart_endpoint("MonetaryPolicy", "summary") == "http://127.0.0.1:8000/api/monetary-policy/summary"
    assert build_chart_endpoint("GlobalFlows", "summary") == "http://127.0.0.1:8000/api/global-flows/summary"
    assert build_chart_endpoint("HousingCredit", "summary") == "http://127.0.0.1:8000/api/housing-credit/summary"
