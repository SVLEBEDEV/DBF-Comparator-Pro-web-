from pydantic import BaseModel, Field


class FilePreviewMetadata(BaseModel):
    name: str
    size_bytes: int
    encoding: str | None = None
    fields: list[str] = Field(default_factory=list)


class ComparisonUploadResponse(BaseModel):
    job_id: str
    status: str
    files: list[FilePreviewMetadata]


class ComparisonRunRequest(BaseModel):
    key1: str = Field(min_length=1)
    key2: str | None = None
    structure_only: bool = False
    check_field_order: bool = False


class ComparisonRunResponse(BaseModel):
    job_id: str
    status: str


class ComparisonSummaryPayload(BaseModel):
    file1_row_count: int | None = None
    file2_row_count: int | None = None
    common_field_count: int | None = None
    missing_fields_count: int = 0
    extra_fields_count: int = 0
    type_mismatches_count: int = 0
    field_order_mismatches_count: int = 0
    duplicate_keys_count_file1: int = 0
    duplicate_keys_count_file2: int = 0
    missing_rows_count: int = 0
    extra_rows_count: int = 0
    data_differences_count: int = 0
    has_differences: bool = False


class ComparisonCategoryItem(BaseModel):
    code: str
    label: str
    count: int
    status: str


class ComparisonReportInfo(BaseModel):
    ready: bool = False
    download_url: str | None = None


class ComparisonStatusResponse(BaseModel):
    job_id: str
    status: str
    key1: str | None = None
    key2: str | None = None
    structure_only: bool = False
    check_field_order: bool = False
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    summary: ComparisonSummaryPayload | None = None
    categories: list[ComparisonCategoryItem] = Field(default_factory=list)
    report: ComparisonReportInfo = Field(default_factory=ComparisonReportInfo)


class PreviewRow(BaseModel):
    values: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ComparisonPreviewResponse(BaseModel):
    job_id: str
    section: str
    limit: int
    offset: int
    total: int
    rows: list[PreviewRow] = Field(default_factory=list)


class DeleteComparisonResponse(BaseModel):
    job_id: str
    status: str
