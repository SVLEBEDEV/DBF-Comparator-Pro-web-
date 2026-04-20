from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.schemas.comparison import (
    ComparisonPreviewResponse,
    ComparisonRunRequest,
    ComparisonRunResponse,
    ComparisonStatusResponse,
    ComparisonSummaryPayload,
    ComparisonUploadResponse,
    DeleteComparisonResponse,
)
from app.services.comparison_jobs import ComparisonJobService
from app.services.dbf_preview import DBFPreviewError, DBFPreviewService
from app.services.temp_storage import TempStorageService
from app.services.uploads import UploadService


router = APIRouter()
settings = get_settings()


@router.post("/uploads", response_model=ComparisonUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_comparison_files(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ComparisonUploadResponse:
    storage_service = TempStorageService(settings)
    preview_service = DBFPreviewService()
    upload_service = UploadService(db=db, storage_service=storage_service, preview_service=preview_service)

    try:
        return upload_service.create_job(file1=file1, file2=file2)
    except DBFPreviewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{job_id}/run", response_model=ComparisonRunResponse)
def run_comparison(
    job_id: UUID,
    payload: ComparisonRunRequest,
    db: Session = Depends(get_db),
) -> ComparisonRunResponse:
    service = ComparisonJobService(db)
    try:
        return service.run_job(job_id=job_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=ComparisonStatusResponse)
def get_comparison_status(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> ComparisonStatusResponse:
    service = ComparisonJobService(db)
    try:
        return service.get_job_status(job_id=job_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{job_id}/summary", response_model=ComparisonSummaryPayload)
def get_comparison_summary(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> ComparisonSummaryPayload:
    service = ComparisonJobService(db)
    try:
        return service.get_summary(job_id=job_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{job_id}/preview", response_model=ComparisonPreviewResponse)
def get_comparison_preview(
    job_id: UUID,
    section: str = Query(...),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ComparisonPreviewResponse:
    service = ComparisonJobService(db)
    try:
        return service.get_preview(job_id=job_id, section=section, limit=limit, offset=offset)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{job_id}/report")
def download_comparison_report(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    service = ComparisonJobService(db)
    try:
        job_status = service.get_job_status(job_id=job_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if not job_status.report.ready or not job_status.report.download_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Excel-отчет еще не готов.")

    job = service.repository.get_job(job_id)
    if job is None or not job.report_temp_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Excel-отчет не найден.")

    return FileResponse(
        path=job.report_temp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"comparison-{job_id}.xlsx",
    )


@router.delete("/{job_id}", response_model=DeleteComparisonResponse)
def delete_comparison(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> DeleteComparisonResponse:
    service = ComparisonJobService(db)
    try:
        return service.cleanup_job(job_id=job_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
