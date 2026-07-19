from fastapi import FastAPI

from src.api.routers.home import router as home_router
from src.api.routers.macro_pulse import router as macro_pulse_router
from src.api.routers.monetary_policy import router as monetary_policy_router
from src.api.routers.housing_credit import router as housing_credit_router
from src.api.routers.financial_markets import router as financial_markets_router
from src.api.routers.global_flows import router as global_flows_router

app = FastAPI(title='MACRO UK DASHBOARD API')


@app.get('/')
def read_root():
    return {'message': 'Welcome to the Macro UK Dashboard API. Head to /docs for the interactive UI.'}


app.include_router(macro_pulse_router, prefix='/api/macropulse', tags=['Macro Pulse'])
app.include_router(home_router, prefix='/api/home', tags=['Home'])
app.include_router(monetary_policy_router, prefix='/api/monetary-policy', tags=['Monetary Policy'])
app.include_router(housing_credit_router, prefix='/api/housing-credit', tags=['Housing and Credit'])
app.include_router(financial_markets_router, prefix='/api/financial-markets', tags=['Financial Markets'])
app.include_router(global_flows_router, prefix='/api/global-flows', tags=['Currency, Commodities and Fixed Income'])

# python -m uvicorn src.api.main:app --reload
