from src.utilities.config_loader import load_config
from datetime import datetime

# Helpers
base_api_endpoint = load_config('endpoints', 'base', 'fastapi')


def build_ons(metric: str):
    base_url = load_config('endpoints', 'base', 'ons')
    metric_config = load_config('metric_manifest', 'ons_metrics', metric)

    return base_url.format(metric_config['topic'], metric_config['cdid'], metric_config['dataset'])


def build_chart_endpoint(section, chart_id):
    section_map = {
        "Home": "home",
        "MacroPulse": "macropulse",
        "MonetaryPolicy": "monetary-policy",
        "HousingCredit": "housing-credit",
        "FinancialMarkets": "financial-markets",
        "GlobalFlows": "global-flows",
    }
    path_section = section_map.get(section, section.lower())
    return f"{base_api_endpoint}/{path_section}/{chart_id.lower()}"



if __name__ == '__main__':
    print(build_chart_endpoint('MacroPulse', 'EGM'))

    # python -m src.utilities.build_url