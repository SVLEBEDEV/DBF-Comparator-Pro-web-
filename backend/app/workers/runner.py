from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings
from app.workers.tasks import process_comparison_job


_desktop_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="comparison-worker")


def enqueue_comparison_job(job_id: str) -> None:
    settings = get_settings()
    if settings.job_runner == "thread":
        _desktop_executor.submit(process_comparison_job, job_id)
        return

    try:
        process_comparison_job.delay(job_id)
    except Exception:  # noqa: BLE001
        process_comparison_job.run(job_id)
