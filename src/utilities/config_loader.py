from pathlib import Path
import yaml

def load_config(yaml_file, source: str = None, name = None):
    file_path = Path('configs') / (yaml_file + '.yaml')

    with open(file_path, 'r') as data:
        content = yaml.safe_load(data)

    # Scenario 1: No source provided -> Return everything (one level up)
    if source is None:
        return content

    # Scenario 2: Source is provided, but no specific name -> Return the source's config
    if name is None:
        return content.get(source)
    
    # Scenario 3: Both source and name are provided
    source_content = content.get(source)
    if source_content is None:
        return None
        
    return source_content.get(name)