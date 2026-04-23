import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ComparisonJob(Base):
    __tablename__ = "comparison_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    file1_original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file2_original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file1_temp_path: Mapped[str] = mapped_column(Text, nullable=False)
    file2_temp_path: Mapped[str] = mapped_column(Text, nullable=False)
    file1_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file2_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file1_encoding: Mapped[str | None] = mapped_column(String(32))
    file2_encoding: Mapped[str | None] = mapped_column(String(32))
    key1: Mapped[str | None] = mapped_column(String(255))
    key2: Mapped[str | None] = mapped_column(String(255))
    structure_only: Mapped[bool] = mapped_column(nullable=False, default=False)
    check_field_order: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    report_temp_path: Mapped[str | None] = mapped_column(Text)
    report_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    report_checksum: Mapped[str | None] = mapped_column(String(128))

    summary: Mapped["ComparisonSummary"] = relationship(back_populates="job", uselist=False)
    artifacts: Mapped[list["ComparisonArtifact"]] = relationship(back_populates="job")
    events: Mapped[list["ComparisonEvent"]] = relationship(back_populates="job")
