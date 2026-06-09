from src.utilities.config_loader import load_config
from datetime import datetime



def build_ons(metric: str):
    base_url = load_config('endpoints', 'base', 'ons')
    metric_config = load_config('metric_manifest', 'ons_metrics', metric)

    return base_url.format(metric_config['topic'], metric_config['cdid'], metric_config['dataset'])


if __name__ == '__main__':
    pass

    #python -m src.utilities.build_url