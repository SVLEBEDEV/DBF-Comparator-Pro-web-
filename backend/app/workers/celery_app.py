from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "dbf_comparator_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.task_ignore_result = True
celery_app.conf.beat_schedule = {
    "cleanup-expired-jobs-hourly": {
        "task": "comparison.cleanup_expired",
        "schedule": crontab(minute=0),
    }
}

# Ensure the worker registers application tasks when started via
# `celery -A app.workers.celery_app.celery_app worker`.
from app.workers import tasks  # noqa: F401,E402
