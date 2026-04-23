from uuid import UUID

from app.core.config import get_settings
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.repositories.comparison_jobs import ComparisonJobRepository
from app.services.comparison_engine import ComparisonEngine, ComparisonValidationError
from app.services.reporting import ExcelReportGenerator
from app.services.strict_dbf_reader import StrictDBFReadError
from app.services.temp_storage import TempStorageService
from app.workers.celery_app import celery_app


@celery_app.task(name="comparison.process")
def process_comparison_job(job_id: str) -> None:
    db = SessionLocal()
    repository = ComparisonJobRepository(db)
    storage = TempStorageService(get_settings())

    try:
        job = repository.get_job(UUID(job_id))
        if job is None:
            return

        repository.mark_processing(job=job)
        repository.add_event(job_id=job.id, event_type="comparison_started", payload_json={})
        db.commit()

        result = ComparisonEngine().run(
            file1_path=job.file1_temp_path,
            file2_path=job.file2_temp_path,
            key1=job.key1 or "",
            key2=job.key2,
            structure_only=job.structure_only,
            check_field_order=job.check_field_order,
        )

        preview_artifact = storage.save_json(result.preview, prefix=f"{job.id}-preview")
        repository.add_artifact(
            job_id=job.id,
            artifact_type="preview_json",
            storage_path=str(preview_artifact.path),
            content_type="application/json",
            size_bytes=preview_artifact.size_bytes,
            expires_at=preview_artifact.expires_at,
        )
        report_path = storage.allocate_path(prefix=f"{job.id}-report", suffix=".xlsx")
        report_size_bytes, report_checksum = ExcelReportGenerator().generate(
            target_path=report_path,
            summary=result.summary,
            preview_payload=result.preview,
        )
        repository.add_artifact(
            job_id=job.id,
            artifact_type="report_xlsx",
            storage_path=str(report_path),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=report_size_bytes,
            expires_at=preview_artifact.expires_at,
        )

        repository.mark_completed(
            job=job,
            summary=result.summary,
            file1_encoding=result.file1_encoding,
            file2_encoding=result.file2_encoding,
            report_temp_path=str(report_path),
            report_size_bytes=report_size_bytes,
            report_checksum=report_checksum,
        )
        repository.add_event(
            job_id=job.id,
            event_type="comparison_completed",
            payload_json={
                "warnings": result.warnings,
                "categories": [item.model_dump() for item in result.categories],
            },
        )
        db.commit()
    except (ComparisonValidationError, StrictDBFReadError) as exc:
        db.rollback()
        job = repository.get_job(UUID(job_id))
        if job is not None:
            error_code = getattr(exc, "code", "comparison_read_error")
            repository.mark_failed(job=job, error_code=error_code, error_message=str(exc))
            repository.add_event(
                job_id=job.id,
                event_type="comparison_failed",
                payload_json={"error_code": error_code},
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = repository.get_job(UUID(job_id))
        if job is not None:
            repository.mark_failed(job=job, error_code="comparison_failed", error_message=str(exc))
            repository.add_event(
                job_id=job.id,
                event_type="comparison_failed",
                payload_json={"error_code": "comparison_failed"},
            )
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="comparison.cleanup_expired")
def cleanup_expired_jobs() -> int:
    db = SessionLocal()
    repository = ComparisonJobRepository(db)
    storage = TempStorageService(get_settings())
    cleaned = 0

    try:
        for job in repository.list_jobs_expired_before(cutoff=utc_now()):
            storage.delete_path(job.file1_temp_path)
            storage.delete_path(job.file2_temp_path)
            storage.delete_path(job.report_temp_path)
            for artifact in repository.delete_artifacts(job_id=job.id):
                storage.delete_path(artifact.storage_path)
            repository.mark_expired(job=job)
            repository.add_event(job_id=job.id, event_type="comparison_expired", payload_json={})
            cleaned += 1
        db.commit()
        return cleaned
    finally:
        db.close()
