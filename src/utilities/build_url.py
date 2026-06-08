from src.utilities.config_loader import load_config
from datetime import datetime



def build_ons(metric: str):
    base_url = load_config('endpoints', 'base', 'ons')
    metric_config = load_config('metric_manifest', 'ons_metrics', metric)

    return base_url.format(metric_config['topic'], metric_config['cdid'], metric_config['dataset'])

def build_boe():
    base_url = load_config('endpoints', 'base', 'boe')

    metric_config = load_config('metric_manifest', 'boe_metrics')
    metric_string_list = []

    for m_id, meta in metric_config.items():
        code = meta.get('series_code', None)

        if code is not None:
            metric_string_list.append(code)
    
    metric_str = ",".join(metric_string_list)
        
    from_date = '01/Jan/1989'
    to_date = datetime.now().strftime("%d/%b/%Y")
    
    return base_url.format(from_date, to_date, metric_str)


if __name__ == '__main__':
    print(build_boe())

    #python -m src.utilities.build_url