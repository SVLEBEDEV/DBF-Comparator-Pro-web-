import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ComparisonSummary(Base):
    __tablename__ = "comparison_summaries"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comparison_jobs.id"), primary_key=True)
    file1_row_count: Mapped[int | None] = mapped_column(BigInteger)
    file2_row_count: Mapped[int | None] = mapped_column(BigInteger)
    common_field_count: Mapped[int | None] = mapped_column(Integer)
    missing_fields_count: Mapped[int | None] = mapped_column(Integer)
    extra_fields_count: Mapped[int | None] = mapped_column(Integer)
    type_mismatches_count: Mapped[int | None] = mapped_column(Integer)
    field_order_mismatches_count: Mapped[int | None] = mapped_column(Integer)
    duplicate_keys_count_file1: Mapped[int | None] = mapped_column(Integer)
    duplicate_keys_count_file2: Mapped[int | None] = mapped_column(Integer)
    missing_rows_count: Mapped[int | None] = mapped_column(BigInteger)
    extra_rows_count: Mapped[int | None] = mapped_column(BigInteger)
    data_differences_count: Mapped[int | None] = mapped_column(BigInteger)
    has_differences: Mapped[bool | None] = mapped_column(Boolean)

    job: Mapped["ComparisonJob"] = relationship(back_populates="summary")
