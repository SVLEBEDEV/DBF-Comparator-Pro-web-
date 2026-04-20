from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import utc_now
from app.models.artifact import ComparisonArtifact
from app.models.event import ComparisonEvent
from app.models.job import ComparisonJob
from app.models.summary import ComparisonSummary
from app.schemas.comparison import ComparisonCategoryItem, ComparisonSummaryPayload


class ComparisonJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def create_uploaded_job(
        self,
        *,
        file1_original_name: str,
        file2_original_name: str,
        file1_temp_path: str,
        file2_temp_path: str,
        file1_size_bytes: int,
        file2_size_bytes: int,
        file1_encoding: str | None,
        file2_encoding: str | None,
    ) -> ComparisonJob:
        now = utc_now()
        job = ComparisonJob(
            status="ready_for_run",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=self.settings.artifact_ttl_hours),
            file1_original_name=file1_original_name,
            file2_original_name=file2_original_name,
            file1_temp_path=file1_temp_path,
            file2_temp_path=file2_temp_path,
            file1_size_bytes=file1_size_bytes,
            file2_size_bytes=file2_size_bytes,
            file1_encoding=file1_encoding,
            file2_encoding=file2_encoding,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def add_artifact(
        self,
        *,
        job_id,
        artifact_type: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        expires_at: datetime,
    ) -> ComparisonArtifact:
        artifact = ComparisonArtifact(
            job_id=job_id,
            artifact_type=artifact_type,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            expires_at=expires_at,
        )
        self.db.add(artifact)
        self.db.flush()
        return artifact

    def get_job(self, job_id: UUID) -> ComparisonJob | None:
        return self.db.get(ComparisonJob, job_id)

    def mark_as_queued(
        self,
        *,
        job: ComparisonJob,
        key1: str,
        key2: str | None,
        structure_only: bool,
        check_field_order: bool,
    ) -> ComparisonJob:
        job.key1 = key1
        job.key2 = key2
        job.structure_only = structure_only
        job.check_field_order = check_field_order
        job.status = "queued"
        job.error_code = None
        job.error_message = None
        job.updated_at = utc_now()
        self.db.add(job)
        self.db.flush()
        return job

    def mark_processing(self, *, job: ComparisonJob) -> ComparisonJob:
        job.status = "processing"
        job.updated_at = utc_now()
        self.db.add(job)
        self.db.flush()
        return job

    def mark_completed(
        self,
        *,
        job: ComparisonJob,
        summary: ComparisonSummaryPayload,
        file1_encoding: str | None,
        file2_encoding: str | None,
        report_temp_path: str | None = None,
        report_size_bytes: int | None = None,
        report_checksum: str | None = None,
    ) -> ComparisonJob:
        job.status = "completed"
        job.updated_at = utc_now()
        job.file1_encoding = file1_encoding
        job.file2_encoding = file2_encoding
        job.report_temp_path = report_temp_path
        job.report_size_bytes = report_size_bytes
        job.report_checksum = report_checksum
        self.db.add(job)
        self.upsert_summary(job_id=job.id, summary=summary)
        self.db.flush()
        return job

    def mark_failed(self, *, job: ComparisonJob, error_code: str, error_message: str) -> ComparisonJob:
        job.status = "failed"
        job.error_code = error_code
        job.error_message = error_message
        job.updated_at = utc_now()
        self.db.add(job)
        self.db.flush()
        return job

    def upsert_summary(self, *, job_id: UUID, summary: ComparisonSummaryPayload) -> ComparisonSummary:
        entity = self.db.get(ComparisonSummary, job_id)
        if entity is None:
            entity = ComparisonSummary(job_id=job_id)

        entity.file1_row_count = summary.file1_row_count
        entity.file2_row_count = summary.file2_row_count
        entity.common_field_count = summary.common_field_count
        entity.missing_fields_count = summary.missing_fields_count
        entity.extra_fields_count = summary.extra_fields_count
        entity.type_mismatches_count = summary.type_mismatches_count
        entity.field_order_mismatches_count = summary.field_order_mismatches_count
        entity.duplicate_keys_count_file1 = summary.duplicate_keys_count_file1
        entity.duplicate_keys_count_file2 = summary.duplicate_keys_count_file2
        entity.missing_rows_count = summary.missing_rows_count
        entity.extra_rows_count = summary.extra_rows_count
        entity.data_differences_count = summary.data_differences_count
        entity.has_differences = summary.has_differences
        self.db.add(entity)
        self.db.flush()
        return entity

    def add_event(self, *, job_id: UUID, event_type: str, payload_json: dict) -> ComparisonEvent:
        event = ComparisonEvent(job_id=job_id, event_type=event_type, payload_json=payload_json)
        self.db.add(event)
        self.db.flush()
        return event

    def get_latest_categories(self, *, job_id: UUID) -> list[ComparisonCategoryItem]:
        event = self.get_latest_completed_event(job_id=job_id)
        if event is None:
            return []
        categories = event.payload_json.get("categories", [])
        return [ComparisonCategoryItem.model_validate(item) for item in categories]

    def get_latest_completed_event(self, *, job_id: UUID) -> ComparisonEvent | None:
        event = (
            self.db.query(ComparisonEvent)
            .filter(ComparisonEvent.job_id == job_id, ComparisonEvent.event_type == "comparison_completed")
            .order_by(ComparisonEvent.created_at.desc(), ComparisonEvent.id.desc())
            .first()
        )
        return event

    def get_artifact(self, *, job_id: UUID, artifact_type: str) -> ComparisonArtifact | None:
        return (
            self.db.query(ComparisonArtifact)
            .filter(
                and_(
                    ComparisonArtifact.job_id == job_id,
                    ComparisonArtifact.artifact_type == artifact_type,
                )
            )
            .order_by(ComparisonArtifact.expires_at.desc(), ComparisonArtifact.id.desc())
            .first()
        )

    def delete_artifacts(self, *, job_id: UUID) -> list[ComparisonArtifact]:
        artifacts = self.db.query(ComparisonArtifact).filter(ComparisonArtifact.job_id == job_id).all()
        for artifact in artifacts:
            self.db.delete(artifact)
        self.db.flush()
        return artifacts

    def mark_expired(self, *, job: ComparisonJob) -> ComparisonJob:
        job.status = "expired"
        job.updated_at = utc_now()
        self.db.add(job)
        self.db.flush()
        return job

    def list_jobs_expired_before(self, *, cutoff: datetime) -> list[ComparisonJob]:
        return (
            self.db.query(ComparisonJob)
            .filter(ComparisonJob.expires_at <= cutoff, ComparisonJob.status != "expired")
            .all()
        )
