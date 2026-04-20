from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.services.runtime_checks import check_database, check_redis, check_storage


router = APIRouter()
settings = get_settings()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, object]:
    checks: dict[str, dict[str, str]] = {}

    try:
        checks["database"] = check_database(db)
        checks["redis"] = check_redis(settings.redis_url)
        checks["storage"] = check_storage(settings.temp_storage_root)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "reason": str(exc), "checks": checks},
        ) from exc

    return {"status": "ok", "checks": checks}
