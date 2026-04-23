from uuid import UUID
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.comparison_jobs import ComparisonJobRepository
from app.schemas.comparison import (
    ComparisonPreviewResponse,
    ComparisonReportInfo,
    ComparisonRunRequest,
    ComparisonRunResponse,
    ComparisonStatusResponse,
    ComparisonSummaryPayload,
    DeleteComparisonResponse,
    PreviewRow,
)
from app.services.temp_storage import TempStorageService
from app.workers.runner import enqueue_comparison_job


class ComparisonJobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ComparisonJobRepository(db)
        self.settings = get_settings()
        self.storage = TempStorageService(self.settings)

    def run_job(self, *, job_id: UUID, payload: ComparisonRunRequest) -> ComparisonRunResponse:
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("Задание не найдено.")
        if job.status not in {"ready_for_run", "failed", "completed"}:
            raise ValueError("Задание уже выполняется или недоступно для повторного запуска.")

        queued_job = self.repository.mark_as_queued(
            job=job,
            key1=payload.key1,
            key2=payload.key2,
            structure_only=payload.structure_only,
            check_field_order=payload.check_field_order,
        )
        self.repository.add_event(
            job_id=queued_job.id,
            event_type="comparison_queued",
            payload_json={
                "key1": payload.key1,
                "key2": payload.key2,
                "structure_only": payload.structure_only,
                "check_field_order": payload.check_field_order,
            },
        )
        self.db.commit()
        enqueue_comparison_job(str(queued_job.id))
        return ComparisonRunResponse(job_id=str(queued_job.id), status=queued_job.status)

    def get_job_status(self, *, job_id: UUID) -> ComparisonStatusResponse:
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("Задание не найдено.")

        warnings = [
            "Сравнение выполняется без нормализации значений: скрытые символы и пробелы считаются различиями."
        ]
        completed_event = self.repository.get_latest_completed_event(job_id=job.id)
        if completed_event is not None:
            warnings = completed_event.payload_json.get("warnings", warnings)
        categories = self.repository.get_latest_categories(job_id=job.id)

        summary = None
        if job.summary is not None:
            summary = ComparisonSummaryPayload(
                file1_row_count=job.summary.file1_row_count,
                file2_row_count=job.summary.file2_row_count,
                common_field_count=job.summary.common_field_count,
                missing_fields_count=job.summary.missing_fields_count or 0,
                extra_fields_count=job.summary.extra_fields_count or 0,
                type_mismatches_count=job.summary.type_mismatches_count or 0,
                field_order_mismatches_count=job.summary.field_order_mismatches_count or 0,
                duplicate_keys_count_file1=job.summary.duplicate_keys_count_file1 or 0,
                duplicate_keys_count_file2=job.summary.duplicate_keys_count_file2 or 0,
                missing_rows_count=job.summary.missing_rows_count or 0,
                extra_rows_count=job.summary.extra_rows_count or 0,
                data_differences_count=job.summary.data_differences_count or 0,
                has_differences=bool(job.summary.has_differences),
            )

        return ComparisonStatusResponse(
            job_id=str(job.id),
            status=job.status,
            key1=job.key1,
            key2=job.key2,
            structure_only=job.structure_only,
            check_field_order=job.check_field_order,
            warnings=warnings,
            error_code=job.error_code,
            error_message=job.error_message,
            summary=summary,
            categories=categories,
            report=ComparisonReportInfo(
                ready=bool(job.report_temp_path and job.status == "completed"),
                download_url=f"{self.settings.api_v1_prefix}/comparisons/{job.id}/report" if job.report_temp_path else None,
            ),
        )

    def get_summary(self, *, job_id: UUID) -> ComparisonSummaryPayload:
        job = self.repository.get_job(job_id)
        if job is None or job.summary is None:
            raise LookupError("Сводка для задания недоступна.")
        return ComparisonSummaryPayload(
            file1_row_count=job.summary.file1_row_count,
            file2_row_count=job.summary.file2_row_count,
            common_field_count=job.summary.common_field_count,
            missing_fields_count=job.summary.missing_fields_count or 0,
            extra_fields_count=job.summary.extra_fields_count or 0,
            type_mismatches_count=job.summary.type_mismatches_count or 0,
            field_order_mismatches_count=job.summary.field_order_mismatches_count or 0,
            duplicate_keys_count_file1=job.summary.duplicate_keys_count_file1 or 0,
            duplicate_keys_count_file2=job.summary.duplicate_keys_count_file2 or 0,
            missing_rows_count=job.summary.missing_rows_count or 0,
            extra_rows_count=job.summary.extra_rows_count or 0,
            data_differences_count=job.summary.data_differences_count or 0,
            has_differences=bool(job.summary.has_differences),
        )

    def get_preview(self, *, job_id: UUID, section: str, limit: int, offset: int) -> ComparisonPreviewResponse:
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("Задание не найдено.")
        artifact = self.repository.get_artifact(job_id=job_id, artifact_type="preview_json")
        if artifact is None:
            artifact_path = self._find_preview_fallback(job_id)
            if artifact_path is None:
                raise LookupError("Preview для задания недоступен.")
            payload = self.storage.read_json(artifact_path)
        else:
            payload = self.storage.read_json(artifact.storage_path)
        section_rows = payload.get(section, []) if isinstance(payload, dict) else []
        page = section_rows[offset : offset + limit]
        return ComparisonPreviewResponse(
            job_id=str(job_id),
            section=section,
            limit=limit,
            offset=offset,
            total=len(section_rows),
            rows=[PreviewRow(values=row) for row in page],
        )

    def _find_preview_fallback(self, job_id: UUID) -> str | None:
        pattern = f"{job_id}-preview-*.json"
        matches = sorted(Path(self.settings.temp_storage_root).glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
        if not matches:
            return None
        return str(matches[0])

    def cleanup_job(self, *, job_id: UUID) -> DeleteComparisonResponse:
        job = self.repository.get_job(job_id)
        if job is None:
            raise LookupError("Задание не найдено.")
        if job.status == "expired":
            return DeleteComparisonResponse(job_id=str(job.id), status=job.status)

        self.storage.delete_path(job.file1_temp_path)
        self.storage.delete_path(job.file2_temp_path)
        self.storage.delete_path(job.report_temp_path)
        for artifact in self.repository.delete_artifacts(job_id=job.id):
            self.storage.delete_path(artifact.storage_path)
        self.repository.mark_expired(job=job)
        self.db.commit()
        return DeleteComparisonResponse(job_id=str(job.id), status=job.status)
