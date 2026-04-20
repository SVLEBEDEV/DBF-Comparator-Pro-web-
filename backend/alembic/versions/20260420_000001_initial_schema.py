"""Initial schema for comparison jobs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260420_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comparison_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("file1_original_name", sa.String(length=255), nullable=False),
        sa.Column("file2_original_name", sa.String(length=255), nullable=False),
        sa.Column("file1_temp_path", sa.Text(), nullable=False),
        sa.Column("file2_temp_path", sa.Text(), nullable=False),
        sa.Column("file1_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file2_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file1_encoding", sa.String(length=32), nullable=True),
        sa.Column("file2_encoding", sa.String(length=32), nullable=True),
        sa.Column("key1", sa.String(length=255), nullable=True),
        sa.Column("key2", sa.String(length=255), nullable=True),
        sa.Column("structure_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("check_field_order", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("report_temp_path", sa.Text(), nullable=True),
        sa.Column("report_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("report_checksum", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_comparison_jobs_status", "comparison_jobs", ["status"])
    op.create_index("ix_comparison_jobs_created_at", "comparison_jobs", ["created_at"])
    op.create_index("ix_comparison_jobs_expires_at", "comparison_jobs", ["expires_at"])

    op.create_table(
        "comparison_summaries",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comparison_jobs.id"), primary_key=True),
        sa.Column("file1_row_count", sa.BigInteger(), nullable=True),
        sa.Column("file2_row_count", sa.BigInteger(), nullable=True),
        sa.Column("common_field_count", sa.Integer(), nullable=True),
        sa.Column("missing_fields_count", sa.Integer(), nullable=True),
        sa.Column("extra_fields_count", sa.Integer(), nullable=True),
        sa.Column("type_mismatches_count", sa.Integer(), nullable=True),
        sa.Column("field_order_mismatches_count", sa.Integer(), nullable=True),
        sa.Column("duplicate_keys_count_file1", sa.Integer(), nullable=True),
        sa.Column("duplicate_keys_count_file2", sa.Integer(), nullable=True),
        sa.Column("missing_rows_count", sa.BigInteger(), nullable=True),
        sa.Column("extra_rows_count", sa.BigInteger(), nullable=True),
        sa.Column("data_differences_count", sa.BigInteger(), nullable=True),
        sa.Column("has_differences", sa.Boolean(), nullable=True),
    )

    op.create_table(
        "comparison_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comparison_jobs.id"), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_comparison_artifacts_job_id", "comparison_artifacts", ["job_id"])

    op.create_table(
        "comparison_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comparison_jobs.id"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_comparison_events_job_id", "comparison_events", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_comparison_events_job_id", table_name="comparison_events")
    op.drop_table("comparison_events")
    op.drop_index("ix_comparison_artifacts_job_id", table_name="comparison_artifacts")
    op.drop_table("comparison_artifacts")
    op.drop_table("comparison_summaries")
    op.drop_index("ix_comparison_jobs_expires_at", table_name="comparison_jobs")
    op.drop_index("ix_comparison_jobs_created_at", table_name="comparison_jobs")
    op.drop_index("ix_comparison_jobs_status", table_name="comparison_jobs")
    op.drop_table("comparison_jobs")
