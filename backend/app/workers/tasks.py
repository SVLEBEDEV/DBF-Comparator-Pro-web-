from app.workers.celery_app import celery_app
from app.workers.process import cleanup_expired_jobs as cleanup_expired_jobs_sync
from app.workers.process import process_comparison_job as process_comparison_job_sync


@celery_app.task(name="comparison.process")
def process_comparison_job(job_id: str) -> None:
    process_comparison_job_sync(job_id)


@celery_app.task(name="comparison.cleanup_expired")
def cleanup_expired_jobs() -> int:
    return cleanup_expired_jobs_sync()
