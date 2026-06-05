import yaml
from pathlib import Path

def load_config(yaml_file, source: str, name: str):
    file_path = Path('configs') / (yaml_file + '.yaml')

    with open(file_path, 'r') as data:
        content = yaml.safe_load(data)

    for lst in content[source]:
        if lst.get(name, None) is not None:
            return lst.get(name)
    
    return None


if __name__ == '__main__':
    print(load_config('endpoints', 'gov', 'inflation'))
