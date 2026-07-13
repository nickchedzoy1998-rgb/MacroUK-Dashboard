from pydantic import BaseModel, create_model
from datetime import date

from src.utilities.config_loader import load_config

macropulse_config = load_config('charts', 'MacroPulse')


def macro_pulse_schema():
    chart_schemas = {}

    for chart, cfg in macropulse_config.items():
        metrics = cfg['metrics']

        fields = {
            'date': (date, ...),
            'chart': (str, ...) 
        }

        for m in metrics:
            fields[m] = (float, ...)

        dynamic_model = create_model(
            f"{chart}Row",
            __base__=BaseModel,
            **fields
            )
    
        dynamic_model.model_config = {"from_attributes": True}
        
        chart_schemas[chart] = dynamic_model

    return chart_schemas


CHART_SCHEMAS = macro_pulse_schema()

# python -m src.api.schemas.macro_pulse

        

        

