from src.etl.fetch.fetch_boe import main as boe_main
from src.etl.fetch.fetch_ons import main as ons_main
from src.etl.fetch.fetch_markets import main as markets_main
from src.etl.fetch.fetch_land_reg import main as land_reg_main



def _run_step(name, fn):
    print(f"=== Starting {name} ETL ===")
    try:
        fn()
        print(f"=== Completed {name} ETL ===\n")
    except Exception as exc:
        print(f"*** {name} ETL failed: {exc} ***\n")

def main():
    _run_step("BOE", boe_main)
    _run_step("ONS", ons_main)
    _run_step("Yahoo Finance", markets_main)
    _run_step("HMLR", land_reg_main)



if __name__ == "__main__":
    main()

# python -m src.etl.pipeline_runner
