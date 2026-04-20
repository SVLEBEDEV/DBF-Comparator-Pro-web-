from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery("dbf_comparator_worker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_ignore_result = True
celery_app.conf.beat_schedule = {
    "cleanup-expired-jobs-hourly": {
        "task": "comparison.cleanup_expired",
        "schedule": crontab(minute=0),
    }
}
