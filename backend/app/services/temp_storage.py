from datetime import datetime, timedelta
import json
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.time import utc_now


class StoredFile:
    def __init__(self, path: Path, size_bytes: int, expires_at: datetime) -> None:
        self.path = path
        self.size_bytes = size_bytes
        self.expires_at = expires_at


class TempStorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.temp_storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile, slot_name: str) -> StoredFile:
        suffix = Path(upload.filename or "upload.dbf").suffix.lower()
        if suffix != ".dbf":
            raise ValueError(f"{slot_name}: expected a .dbf file")

        target = self.root / f"{uuid4()}{suffix}"
        size_bytes = 0

        with target.open("wb") as file_obj:
            while chunk := upload.file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > self.settings.upload_max_size_bytes:
                    target.unlink(missing_ok=True)
                    raise ValueError(f"{slot_name}: file exceeds upload size limit")
                file_obj.write(chunk)

        return StoredFile(
            path=target,
            size_bytes=size_bytes,
            expires_at=utc_now() + timedelta(hours=self.settings.artifact_ttl_hours),
        )

    def save_json(self, payload: dict | list, *, prefix: str) -> StoredFile:
        target = self.root / f"{prefix}-{uuid4()}.json"
        content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        target.write_bytes(content)
        return StoredFile(
            path=target,
            size_bytes=len(content),
            expires_at=utc_now() + timedelta(hours=self.settings.artifact_ttl_hours),
        )

    def read_json(self, path: str | Path) -> dict | list:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def allocate_path(self, *, prefix: str, suffix: str) -> Path:
        return self.root / f"{prefix}-{uuid4()}{suffix}"

    def delete_path(self, path: str | Path | None) -> None:
        if path is None:
            return
        Path(path).unlink(missing_ok=True)
