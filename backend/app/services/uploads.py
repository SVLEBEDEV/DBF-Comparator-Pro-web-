from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories.comparison_jobs import ComparisonJobRepository
from app.schemas.comparison import ComparisonUploadResponse, FilePreviewMetadata
from app.services.dbf_preview import DBFPreviewService
from app.services.temp_storage import TempStorageService


class UploadService:
    def __init__(
        self,
        *,
        db: Session,
        storage_service: TempStorageService,
        preview_service: DBFPreviewService,
    ) -> None:
        self.db = db
        self.storage_service = storage_service
        self.preview_service = preview_service
        self.repository = ComparisonJobRepository(db)

    def create_job(self, *, file1: UploadFile, file2: UploadFile) -> ComparisonUploadResponse:
        stored1 = self.storage_service.save_upload(file1, "file1")
        stored2 = self.storage_service.save_upload(file2, "file2")

        fields1, encoding1 = self.preview_service.read_fields(stored1.path)
        fields2, encoding2 = self.preview_service.read_fields(stored2.path)

        job = self.repository.create_uploaded_job(
            file1_original_name=file1.filename or "file1.dbf",
            file2_original_name=file2.filename or "file2.dbf",
            file1_temp_path=str(stored1.path),
            file2_temp_path=str(stored2.path),
            file1_size_bytes=stored1.size_bytes,
            file2_size_bytes=stored2.size_bytes,
            file1_encoding=encoding1,
            file2_encoding=encoding2,
        )
        self.repository.add_artifact(
            job_id=job.id,
            artifact_type="uploaded_file",
            storage_path=str(stored1.path),
            content_type=file1.content_type or "application/octet-stream",
            size_bytes=stored1.size_bytes,
            expires_at=stored1.expires_at,
        )
        self.repository.add_artifact(
            job_id=job.id,
            artifact_type="uploaded_file",
            storage_path=str(stored2.path),
            content_type=file2.content_type or "application/octet-stream",
            size_bytes=stored2.size_bytes,
            expires_at=stored2.expires_at,
        )
        self.db.commit()

        return ComparisonUploadResponse(
            job_id=str(job.id),
            status=job.status,
            files=[
                FilePreviewMetadata(
                    name=file1.filename or "file1.dbf",
                    size_bytes=stored1.size_bytes,
                    encoding=encoding1,
                    fields=fields1,
                ),
                FilePreviewMetadata(
                    name=file2.filename or "file2.dbf",
                    size_bytes=stored2.size_bytes,
                    encoding=encoding2,
                    fields=fields2,
                ),
            ],
        )
