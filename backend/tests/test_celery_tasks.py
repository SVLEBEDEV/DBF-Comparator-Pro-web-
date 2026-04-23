from app.workers.celery_app import celery_app


def test_worker_registers_comparison_tasks() -> None:
    assert "comparison.process" in celery_app.tasks
    assert "comparison.cleanup_expired" in celery_app.tasks
