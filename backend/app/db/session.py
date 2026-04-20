from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings


def build_engine(settings: Settings):
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            future=True,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(settings.database_url, future=True, pool_pre_ping=True)


settings = get_settings()
engine = build_engine(settings)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def configure_session_factory(new_settings: Settings) -> None:
    global engine, SessionLocal
    engine = build_engine(new_settings)
    SessionLocal.configure(bind=engine)
