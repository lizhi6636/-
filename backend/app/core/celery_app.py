from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "quant_trading",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.backtest_runner",
        "app.services.snapshot_service",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    task_soft_time_limit=240,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "match-pending-limit-orders": {
        "task": "app.services.simulation_engine.match_pending_orders",
        "schedule": 5.0,
    },
    "update-realtime-prices": {
        "task": "app.services.market_data_service.poll_market_data",
        "schedule": 3.0,
    },
    "daily-account-snapshot": {
        "task": "app.services.snapshot_service.take_daily_snapshots",
        "schedule": crontab(minute=0, hour=15, day_of_week="1-5"),
    },
    "release-t1-shares": {
        "task": "app.services.simulation_engine.release_t1_shares",
        "schedule": crontab(minute=0, hour=9, day_of_week="1-5"),
    },
}
