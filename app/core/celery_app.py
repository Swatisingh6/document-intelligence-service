from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "doc_intel_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes timeout per task
    broker_connection_retry_on_startup=False,
    broker_connection_timeout=1.0  # Fast fallback to sync mode if Redis worker is not running locally
)
