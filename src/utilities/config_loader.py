import yaml
from pathlib import Path

def load_config(yaml_file, source: str, name = None):
    file_path = Path('configs') / (yaml_file + '.yaml')

    with open(file_path, 'r') as data:
        content = yaml.safe_load(data)

    if name is None:
        return content.get(source, None)
    
    return content.get(source, None).get(name, None)


if __name__ == '__main__':
    print(load_config('metric_manifest', 'boe_metrics').keys())