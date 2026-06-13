from fastapi import APIRouter

from app.api.v1 import auth, dashboard, stocks, market_data, simulation, backtest, factor, learn

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(market_data.router, prefix="/market", tags=["Market Data"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtest"])
api_router.include_router(factor.router, prefix="/factors", tags=["Factors"])
api_router.include_router(learn.router, prefix="/learn", tags=["Learn"])
