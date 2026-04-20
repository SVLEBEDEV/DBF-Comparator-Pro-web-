from datetime import datetime
import os
from pathlib import Path
from struct import pack
from tempfile import TemporaryDirectory


def write_dbf(path: Path, fields: list[tuple[str, int]], rows: list[tuple[str, ...]], encoding: str = "cp866") -> None:
    now = datetime.now()
    num_records = len(rows)
    record_length = 1 + sum(length for _, length in fields)
    header_length = 32 + 32 * len(fields) + 1

    with path.open("wb") as handle:
        handle.write(
            pack(
                "<BBBBIHH20x",
                0x03,
                now.year - 1900,
                now.month,
                now.day,
                num_records,
                header_length,
                record_length,
            )
        )
        for name, length in fields:
            name_bytes = name.encode("ascii")[:11].ljust(11, b"\x00")
            handle.write(pack("<11sc4xBB14x", name_bytes, b"C", length, 0))
        handle.write(b"\r")
        for row in rows:
            handle.write(b" ")
            for (_, length), value in zip(fields, row):
                encoded = value.encode(encoding, errors="strict")[:length]
                handle.write(encoded.ljust(length, b" "))
        handle.write(b"\x1a")


def main() -> None:
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        storage_root = tmp_path / "storage"
        db_path = tmp_path / "smoke.sqlite"

        os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        os.environ["TEMP_STORAGE_ROOT"] = str(storage_root)
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["CORS_ORIGINS"] = '["http://localhost:5173","http://localhost:8080"]'

        from app.core.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        import app.db.base  # noqa: F401
        import app.db.session as db_session

        db_session.configure_session_factory(settings)
        db_session.Base.metadata.create_all(bind=db_session.engine)

        import app.api.v1.health as health_module
        import app.services.comparison_jobs as comparison_jobs_module
        from app.main import create_app
        from app.workers.tasks import process_comparison_job
        from fastapi.testclient import TestClient

        health_module.check_redis = lambda redis_url: {"status": "ok"}  # type: ignore[assignment]
        comparison_jobs_module.enqueue_comparison_job = lambda job_id: process_comparison_job.run(job_id)  # type: ignore[assignment]

        file1 = tmp_path / "file1.dbf"
        file2 = tmp_path / "file2.dbf"
        write_dbf(file1, [("ID", 10), ("VALUE", 10)], [("1", "A "), ("2", "B")])
        write_dbf(file2, [("ID", 10), ("VALUE", 10)], [("1", "A\t"), ("3", "C")])

        client = TestClient(create_app())

        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/ready").status_code == 200

        with file1.open("rb") as left, file2.open("rb") as right:
            upload_response = client.post(
                "/api/v1/comparisons/uploads",
                files={
                    "file1": ("file1.dbf", left, "application/octet-stream"),
                    "file2": ("file2.dbf", right, "application/octet-stream"),
                },
            )
        assert upload_response.status_code == 201, upload_response.text
        job_id = upload_response.json()["job_id"]

        run_response = client.post(
            f"/api/v1/comparisons/{job_id}/run",
            json={
                "key1": "ID",
                "key2": None,
                "structure_only": False,
                "check_field_order": False,
            },
        )
        assert run_response.status_code == 200, run_response.text

        status_response = client.get(f"/api/v1/comparisons/{job_id}")
        assert status_response.status_code == 200, status_response.text
        status_payload = status_response.json()
        assert status_payload["status"] == "completed", status_payload
        assert status_payload["summary"]["data_differences_count"] >= 1

        preview_response = client.get(
            f"/api/v1/comparisons/{job_id}/preview",
            params={"section": "DETAILS", "limit": 25, "offset": 0},
        )
        assert preview_response.status_code == 200, preview_response.text
        preview_payload = preview_response.json()
        assert preview_payload["total"] >= 1

        report_response = client.get(f"/api/v1/comparisons/{job_id}/report")
        assert report_response.status_code == 200, report_response.text
        assert report_response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        cleanup_response = client.delete(f"/api/v1/comparisons/{job_id}")
        assert cleanup_response.status_code == 200, cleanup_response.text
        assert cleanup_response.json()["status"] == "expired"

        print("Local smoke passed")


if __name__ == "__main__":
    main()
