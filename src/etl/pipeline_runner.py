from src.etl.fetch.fetch_boe import main as boe_main
from src.etl.fetch.fetch_ons import main as ons_main
from src.etl.fetch.fetch_markets import main as markets_main
from src.etl.fetch.fetch_land_reg import main as land_reg_main
from src.etl.prepare_datasets.home import main as home_kpis
from src.etl.prepare_datasets.macro_pulse import main as macropulse_datasets



def _run_step(name, fn):
    print(f"=== Starting {name} ETL ===")
    try:
        fn()
        print(f"=== Completed {name} ETL ===\n")
    except Exception as exc:
        print(f"*** {name} ETL failed: {exc} ***\n")

def main():
    print('Preparing to extract raw data')
    _run_step("ONS", ons_main)
    _run_step("BOE", boe_main)
    _run_step("Yahoo Finance", markets_main)
    _run_step("HMLR", land_reg_main)

    print('Raw data extraction complete.')

    print('Preparing to transform Datasets...')

    _run_step("Home KPI preparation", home_kpis)
    _run_step("Macro Pulse preparation", macropulse_datasets)

    print('Dataset transformation complete')


if __name__ == "__main__":
    main()

# python -m src.etl.pipeline_runner
