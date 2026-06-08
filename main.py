from src.etl.fetch_ons import main as fetch_ons
from src.api.main import health_check, get_series
from src.utilities.config_loader import load_config

# Helpers
ons_config = load_config('metric_manifest', 'ons_metrics')




def main():
    fetch_ons()
    health_check()

    for m, m_config in ons_config.items():
        get_series(m)
    