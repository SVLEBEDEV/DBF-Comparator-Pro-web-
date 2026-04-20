from hashlib import sha256
from pathlib import Path

import xlsxwriter

from app.schemas.comparison import ComparisonSummaryPayload


SECTION_COLUMNS: dict[str, list[str]] = {
    "STRUCTURE": ["field", "issue", "file"],
    "FIELD_ORDER": ["field", "file1_position", "file2_position"],
    "TYPES": ["field", "file1_type", "file2_type"],
    "DUPLICATES": ["file", "key", "occurrences"],
    "RECONCILIATION": ["issue", "key"],
    "DETAILS": ["key", "field", "file1_value", "file2_value"],
}


class ExcelReportGenerator:
    def generate(
        self,
        *,
        target_path: str | Path,
        summary: ComparisonSummaryPayload,
        preview_payload: dict[str, list[dict[str, object]]],
    ) -> tuple[int, str]:
        destination = Path(target_path)
        workbook = xlsxwriter.Workbook(destination)

        self._write_summary(workbook, summary)
        for section in ["STRUCTURE", "FIELD_ORDER", "TYPES", "DUPLICATES", "RECONCILIATION", "DETAILS"]:
            self._write_section(workbook, section=section, rows=preview_payload.get(section, []))

        workbook.close()
        payload = destination.read_bytes()
        return len(payload), sha256(payload).hexdigest()

    def _write_summary(self, workbook: xlsxwriter.Workbook, summary: ComparisonSummaryPayload) -> None:
        worksheet = workbook.add_worksheet("SUMMARY")
        headers = [
            ("file1_row_count", summary.file1_row_count),
            ("file2_row_count", summary.file2_row_count),
            ("common_field_count", summary.common_field_count),
            ("missing_fields_count", summary.missing_fields_count),
            ("extra_fields_count", summary.extra_fields_count),
            ("type_mismatches_count", summary.type_mismatches_count),
            ("field_order_mismatches_count", summary.field_order_mismatches_count),
            ("duplicate_keys_count_file1", summary.duplicate_keys_count_file1),
            ("duplicate_keys_count_file2", summary.duplicate_keys_count_file2),
            ("missing_rows_count", summary.missing_rows_count),
            ("extra_rows_count", summary.extra_rows_count),
            ("data_differences_count", summary.data_differences_count),
            ("has_differences", summary.has_differences),
        ]
        worksheet.write_row(0, 0, ["metric", "value"])
        for index, (name, value) in enumerate(headers, start=1):
            worksheet.write(index, 0, name)
            worksheet.write(index, 1, value)

    def _write_section(self, workbook: xlsxwriter.Workbook, *, section: str, rows: list[dict[str, object]]) -> None:
        worksheet = workbook.add_worksheet(section)
        columns = SECTION_COLUMNS[section]
        worksheet.write_row(0, 0, columns)
        for row_index, row in enumerate(rows, start=1):
            worksheet.write_row(row_index, 0, [self._stringify(row.get(column)) for column in columns])

    def _stringify(self, value: object) -> object:
        if value is None:
            return ""
        return value
