"""Run the complete required extraction and preparation pipeline."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from src.etl.fetch.fetch_boe import main as boe_main
from src.etl.fetch.fetch_land_reg import main as land_reg_main
from src.etl.fetch.fetch_markets import main as markets_main
from src.etl.fetch.fetch_ons import main as ons_main
from src.etl.prepare_datasets.financial_markets import main as financial_markets_datasets
from src.etl.prepare_datasets.global_flows import main as global_flows_datasets
from src.etl.prepare_datasets.home import main as home_kpis
from src.etl.prepare_datasets.housing_credit import main as housing_credit_datasets
from src.etl.prepare_datasets.macro_pulse import main as macro_pulse_datasets
from src.etl.prepare_datasets.monetary_policy import main as monetary_policy_datasets


PipelineStep = tuple[str, Callable[[], object]]

EXTRACTION_STEPS: tuple[PipelineStep, ...] = (
    ("ONS extraction", ons_main),
    ("Bank of England extraction", boe_main),
    ("Yahoo Finance extraction", markets_main),
    ("HM Land Registry extraction", land_reg_main),
)

PREPARATION_STEPS: tuple[PipelineStep, ...] = (
    ("Home KPI preparation", home_kpis),
    ("Macro Pulse preparation", macro_pulse_datasets),
    ("Monetary Policy preparation", monetary_policy_datasets),
    ("Housing Credit preparation", housing_credit_datasets),
    ("Financial Markets preparation", financial_markets_datasets),
    ("Global Flows preparation", global_flows_datasets),
)


class PipelineStepError(RuntimeError):
    """Raised when a required pipeline stage fails."""


def run_step(name: str, function: Callable[[], object]) -> None:
    print(f"=== Starting {name} ===")
    try:
        function()
    except Exception as exc:
        raise PipelineStepError(f"{name} failed: {exc}") from exc
    print(f"=== Completed {name} ===")


def run_pipeline(
    extraction_steps: Sequence[PipelineStep] = EXTRACTION_STEPS,
    preparation_steps: Sequence[PipelineStep] = PREPARATION_STEPS,
) -> None:
    print("Starting MacroUK warehouse pipeline")
    for name, function in extraction_steps:
        run_step(name, function)
    for name, function in preparation_steps:
        run_step(name, function)
    print("MacroUK warehouse pipeline completed successfully")


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
