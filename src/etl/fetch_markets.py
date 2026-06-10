import yfinance as yf

from src.utilities.config_loader import load_config

# Helpers
y_config = load_config('metric_manifest', 'y_finance_metrics')

def extract(m, m_config):
    "Pass in a single dict from the config into the function in main"
    ticker = yf.Ticker(m_config.get('ticker', None))

    if ticker is not None:
        if m == 'GILT_10Y_INDEX':
            period = '5d'
        else:
            period = 'max'
        
        history = ticker.history(period=period)
    
    return history


def main() -> dict:
    "Returns a list of [{name}_df: pd.dataframe], ..."
    dataframes = []

    for m, m_config in y_config.items():
        data = extract(m=m, m_config=m_config)

        if not data.empty:

            dataframes.append({
                f'{m}_df': data
                }
            )
    
    if not dataframes:
        print('No Data to Return')
        return
    
    return dataframes
    

if __name__ == '__main__':
    print(main())

    # python -m src.etl.fetch_markets