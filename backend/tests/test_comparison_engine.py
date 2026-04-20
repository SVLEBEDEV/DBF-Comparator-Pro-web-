from app.services.comparison_engine import ComparisonEngine
from app.schemas.comparison import ComparisonSummaryPayload
from app.services.reporting import ExcelReportGenerator
from app.services.strict_dbf_reader import DBFFieldDefinition, DBFTableData


class FakeReader:
    def __init__(self, tables: list[DBFTableData]) -> None:
        self.tables = tables

    def read_table(self, path: str) -> DBFTableData:
        return self.tables.pop(0)


def build_table(*, fields: list[DBFFieldDefinition], records: list[dict[str, object]]) -> DBFTableData:
    return DBFTableData(encoding="cp866", fields=fields, records=records)


def test_comparison_engine_calculates_schema_duplicates_and_reconciliation() -> None:
    engine = ComparisonEngine(
        reader=FakeReader(
            [
                build_table(
                    fields=[
                        DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0),
                        DBFFieldDefinition(name="NAME", type="C", length=20, decimal_count=0),
                    ],
                    records=[
                        {"ID": "1", "NAME": "Alice"},
                        {"ID": "1", "NAME": "Alice duplicate"},
                        {"ID": "2", "NAME": "Bob"},
                    ],
                ),
                build_table(
                    fields=[
                        DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0),
                        DBFFieldDefinition(name="SURNAME", type="C", length=20, decimal_count=0),
                    ],
                    records=[
                        {"ID": "2", "SURNAME": "Bob"},
                        {"ID": "3", "SURNAME": "Charlie"},
                    ],
                ),
            ]
        )
    )

    result = engine.run(
        file1_path="file1.dbf",
        file2_path="file2.dbf",
        key1="ID",
        key2=None,
        structure_only=False,
        check_field_order=False,
    )

    assert result.summary.missing_fields_count == 1
    assert result.summary.extra_fields_count == 1
    assert result.summary.duplicate_keys_count_file1 == 1
    assert result.summary.duplicate_keys_count_file2 == 0
    assert result.summary.missing_rows_count == 1
    assert result.summary.extra_rows_count == 1
    assert result.summary.has_differences is True


def test_comparison_engine_skips_row_analysis_in_structure_only_mode() -> None:
    shared_fields = [DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0)]
    engine = ComparisonEngine(
        reader=FakeReader(
            [
                build_table(fields=shared_fields, records=[{"ID": "1"}, {"ID": "1"}]),
                build_table(fields=shared_fields, records=[{"ID": "2"}]),
            ]
        )
    )

    result = engine.run(
        file1_path="file1.dbf",
        file2_path="file2.dbf",
        key1="ID",
        key2=None,
        structure_only=True,
        check_field_order=False,
    )

    assert result.summary.duplicate_keys_count_file1 == 0
    assert result.summary.duplicate_keys_count_file2 == 0
    assert result.summary.missing_rows_count == 0
    assert result.summary.extra_rows_count == 0


def test_comparison_engine_detects_hidden_symbol_differences_without_normalization() -> None:
    shared_fields = [
        DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0),
        DBFFieldDefinition(name="VALUE", type="C", length=20, decimal_count=0),
    ]
    engine = ComparisonEngine(
        reader=FakeReader(
            [
                build_table(fields=shared_fields, records=[{"ID": "1", "VALUE": "A "}]),
                build_table(fields=shared_fields, records=[{"ID": "1", "VALUE": "A\t"}]),
            ]
        )
    )

    result = engine.run(
        file1_path="file1.dbf",
        file2_path="file2.dbf",
        key1="ID",
        key2=None,
        structure_only=False,
        check_field_order=False,
    )

    assert result.summary.data_differences_count == 1
    assert result.preview["DETAILS"][0]["file1_value"] == "A "
    assert result.preview["DETAILS"][0]["file2_value"] == "A\t"


def test_comparison_engine_detects_field_order_mismatches_for_full_schema() -> None:
    engine = ComparisonEngine(
        reader=FakeReader(
            [
                build_table(
                    fields=[
                        DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0),
                        DBFFieldDefinition(name="NAME", type="C", length=20, decimal_count=0),
                    ],
                    records=[],
                ),
                build_table(
                    fields=[
                        DBFFieldDefinition(name="ID", type="C", length=10, decimal_count=0),
                        DBFFieldDefinition(name="SURNAME", type="C", length=20, decimal_count=0),
                        DBFFieldDefinition(name="NAME", type="C", length=20, decimal_count=0),
                    ],
                    records=[],
                ),
            ]
        )
    )

    result = engine.run(
        file1_path="file1.dbf",
        file2_path="file2.dbf",
        key1="ID",
        key2=None,
        structure_only=True,
        check_field_order=True,
    )

    assert result.summary.field_order_mismatches_count == 2
    assert result.preview["FIELD_ORDER"] == [
        {"position": 2, "file1_field": "NAME", "file2_field": "SURNAME"},
        {"position": 3, "file1_field": "", "file2_field": "NAME"},
    ]


def test_excel_report_generator_creates_required_sheets(tmp_path) -> None:
    target = tmp_path / "report.xlsx"
    size_bytes, checksum = ExcelReportGenerator().generate(
        target_path=target,
        summary=ComparisonSummaryPayload(
            file1_row_count=1,
            file2_row_count=1,
            common_field_count=2,
            missing_fields_count=0,
            extra_fields_count=0,
            type_mismatches_count=0,
            field_order_mismatches_count=0,
            duplicate_keys_count_file1=0,
            duplicate_keys_count_file2=0,
            missing_rows_count=0,
            extra_rows_count=0,
            data_differences_count=1,
            has_differences=True,
        ),
        preview_payload={
            "STRUCTURE": [],
            "FIELD_ORDER": [],
            "TYPES": [],
            "DUPLICATES": [],
            "RECONCILIATION": [],
            "DETAILS": [{"key": "1", "field": "VALUE", "file1_value": "A ", "file2_value": "A\t"}],
        },
    )

    assert target.exists()
    assert size_bytes > 0
    assert checksum
