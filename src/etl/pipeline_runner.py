from src.etl.fetch.fetch_boe import main as boe_main
from src.etl.fetch.fetch_ons import main as ons_main
from src.etl.fetch.fetch_markets import main as markets_main
from src.etl.fetch.fetch_land_reg import main as land_reg_main
from src.etl.prepare_datasets.financial_markets import main as financial_markets_datasets
from src.etl.prepare_datasets.global_flows import main as global_flows_datasets
from src.etl.prepare_datasets.home import main as home_kpis
from src.etl.prepare_datasets.housing_credit import main as housing_credit_datasets
from src.etl.prepare_datasets.macro_pulse import main as macropulse_datasets
from src.etl.prepare_datasets.monetary_policy import main as monetary_policy_datasets



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
    _run_step("Monetary Policy preparation", monetary_policy_datasets)
    _run_step("Housing Credit preparation", housing_credit_datasets)
    _run_step("Financial Markets preparation", financial_markets_datasets)
    _run_step("Global Flows preparation", global_flows_datasets)



    print('Dataset transformation complete')


if __name__ == "__main__":
    main()

# python -m src.etl.pipeline_runner
