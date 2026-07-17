from fastapi import FastAPI

from src.api.routers.home import router as home_router
from src.api.routers.macro_pulse import router as macro_pulse_router

app = FastAPI(title='MACRO UK DASHBOARD API')


@app.get('/')
def read_root():
    return {'message': 'Welcome to the Macro UK Dashboard API. Head to /docs for the interactive UI.'}


app.include_router(macro_pulse_router, prefix='/api/macropulse', tags=['Macro Pulse'])
app.include_router(home_router, prefix='/api/home', tags=['Home'])
