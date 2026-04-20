from pathlib import Path

from app.core.config import Settings
from app.services.temp_storage import TempStorageService


def test_temp_storage_json_roundtrip(tmp_path: Path) -> None:
    service = TempStorageService(
        Settings(
            temp_storage_root=tmp_path,
            database_url="sqlite+pysqlite:///:memory:",
            redis_url="redis://localhost:6379/0",
        )
    )

    stored = service.save_json({"DETAILS": [{"field": "VALUE"}]}, prefix="preview")
    payload = service.read_json(stored.path)

    assert payload == {"DETAILS": [{"field": "VALUE"}]}
