from pathlib import Path

from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database(db: Session) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


def check_redis(redis_url: str) -> dict[str, str]:
    client = Redis.from_url(redis_url)
    try:
        client.ping()
    finally:
        client.close()
    return {"status": "ok"}


def check_storage(storage_root: Path) -> dict[str, str]:
    storage_root.mkdir(parents=True, exist_ok=True)
    if not storage_root.exists():
        raise FileNotFoundError(storage_root)
    return {"status": "ok"}
