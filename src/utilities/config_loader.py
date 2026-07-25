from pathlib import Path
from functools import lru_cache
from typing import Mapping

import yaml


def load_config(yaml_file, source: str | None = None, name=None):
    file_path = Path('configs') / (yaml_file + '.yaml')

    with open(file_path, 'r', encoding='utf-8') as data:
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


@lru_cache(maxsize=1)
def _manifest_labels() -> dict[str, str]:
    manifest = load_config("metric_manifest") or {}
    labels: dict[str, str] = {}
    for section in manifest.values():
        if not isinstance(section, Mapping):
            continue
        for metric, metadata in section.items():
            if isinstance(metadata, Mapping) and metadata.get("name"):
                labels[str(metric)] = str(metadata["name"])
    return labels


def resolve_metric_label(metric: str, explicit_labels: Mapping[str, str] | None = None) -> str:
    """Resolve a public label while keeping the raw identifier internal."""
    labels = explicit_labels or {}
    if metric in labels:
        return str(labels[metric])

    base = metric.removesuffix("_normalised")
    if base in labels:
        return str(labels[base])

    lookup = base.removesuffix("_close")
    manifest_label = _manifest_labels().get(lookup) or _manifest_labels().get(base)
    if manifest_label:
        return manifest_label

    cleaned = base
    for suffix in ("_MO", "_DA", "_QOQ", "_YOY"):
        cleaned = cleaned.removesuffix(suffix)
    return cleaned.replace("_", " ").strip().title()
