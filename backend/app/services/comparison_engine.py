from collections import Counter
from dataclasses import dataclass

from app.schemas.comparison import ComparisonCategoryItem, ComparisonSummaryPayload
from app.services.strict_dbf_reader import DBFFieldDefinition, DBFTableData, StrictDBFReader


class ComparisonValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(slots=True)
class ComparisonResult:
    summary: ComparisonSummaryPayload
    categories: list[ComparisonCategoryItem]
    warnings: list[str]
    file1_encoding: str
    file2_encoding: str
    preview: dict[str, list[dict[str, object]]]


class ComparisonEngine:
    def __init__(self, reader: StrictDBFReader | None = None) -> None:
        self.reader = reader or StrictDBFReader()

    def run(
        self,
        *,
        file1_path: str,
        file2_path: str,
        key1: str,
        key2: str | None,
        structure_only: bool,
        check_field_order: bool,
    ) -> ComparisonResult:
        table1 = self.reader.read_table(file1_path)
        table2 = self.reader.read_table(file2_path)

        key_fields = [key1]
        if key2:
            key_fields.append(key2)

        schema_metrics = self._compare_schema(table1.fields, table2.fields, check_field_order=check_field_order)
        warnings = [
            "Сравнение выполняется без нормализации значений: пробелы и скрытые символы считаются значимыми."
        ]

        duplicate_file1 = 0
        duplicate_file2 = 0
        missing_rows_count = 0
        extra_rows_count = 0
        details_count = 0
        preview = self._build_schema_preview(table1.fields, table2.fields, check_field_order=check_field_order)

        if not structure_only:
            self._validate_keys(table1, table2, key_fields)
            duplicate_file1, counts1 = self._analyze_duplicates(table1.records, key_fields)
            duplicate_file2, counts2 = self._analyze_duplicates(table2.records, key_fields)
            key_rows_1 = self._group_rows(table1.records, key_fields)
            key_rows_2 = self._group_rows(table2.records, key_fields)
            keys1 = set(key_rows_1.keys())
            keys2 = set(key_rows_2.keys())
            missing_rows_count = len(keys1 - keys2)
            extra_rows_count = len(keys2 - keys1)
            preview["DUPLICATES"] = self._build_duplicates_preview(counts1, counts2)
            preview["RECONCILIATION"] = self._build_reconciliation_preview(keys1, keys2)
            details_rows = self._build_details_preview(
                key_rows_1=key_rows_1,
                key_rows_2=key_rows_2,
                common_fields=[name for name in [field.name for field in table1.fields] if name in {field.name for field in table2.fields}],
            )
            preview["DETAILS"] = details_rows
            details_count = len(details_rows)

            if duplicate_file1 or duplicate_file2:
                warnings.append("Обнаружены дубликаты ключей. Итоговая сверка по строкам может требовать ручной разбор.")
        else:
            preview["DUPLICATES"] = []
            preview["RECONCILIATION"] = []
            preview["DETAILS"] = []

        summary = ComparisonSummaryPayload(
            file1_row_count=len(table1.records),
            file2_row_count=len(table2.records),
            common_field_count=schema_metrics["common_field_count"],
            missing_fields_count=schema_metrics["missing_fields_count"],
            extra_fields_count=schema_metrics["extra_fields_count"],
            type_mismatches_count=schema_metrics["type_mismatches_count"],
            field_order_mismatches_count=schema_metrics["field_order_mismatches_count"],
            duplicate_keys_count_file1=duplicate_file1,
            duplicate_keys_count_file2=duplicate_file2,
            missing_rows_count=missing_rows_count,
            extra_rows_count=extra_rows_count,
            data_differences_count=details_count,
            has_differences=any(
                (
                    schema_metrics["missing_fields_count"],
                    schema_metrics["extra_fields_count"],
                    schema_metrics["type_mismatches_count"],
                    schema_metrics["field_order_mismatches_count"],
                    duplicate_file1,
                    duplicate_file2,
                    missing_rows_count,
                    extra_rows_count,
                    details_count,
                )
            ),
        )

        categories = [
            self._build_category("STRUCTURE", "Структура", summary.missing_fields_count + summary.extra_fields_count),
            self._build_category("FIELD_ORDER", "Порядок полей", summary.field_order_mismatches_count),
            self._build_category("TYPES", "Типы полей", summary.type_mismatches_count),
            self._build_category("DUPLICATES", "Дубликаты ключей", duplicate_file1 + duplicate_file2),
            self._build_category("RECONCILIATION", "Сверка строк", missing_rows_count + extra_rows_count),
            self._build_category("DETAILS", "Различия значений", details_count),
        ]

        return ComparisonResult(
            summary=summary,
            categories=categories,
            warnings=warnings,
            file1_encoding=table1.encoding,
            file2_encoding=table2.encoding,
            preview=preview,
        )

    def _validate_keys(self, table1: DBFTableData, table2: DBFTableData, key_fields: list[str]) -> None:
        fields1 = {field.name for field in table1.fields}
        fields2 = {field.name for field in table2.fields}
        missing = [field for field in key_fields if field not in fields1 or field not in fields2]
        if missing:
            raise ComparisonValidationError(
                code="missing_key_fields",
                message=f"Ключевые поля отсутствуют в одной из структур: {', '.join(missing)}",
            )

    def _analyze_duplicates(
        self, records: list[dict[str, object]], key_fields: list[str]
    ) -> tuple[int, Counter[tuple[object, ...]]]:
        keys = [tuple(record.get(field) for field in key_fields) for record in records]
        counts = Counter(keys)
        duplicates = sum(1 for count in counts.values() if count > 1)
        return duplicates, counts

    def _compare_schema(
        self,
        fields1: list[DBFFieldDefinition],
        fields2: list[DBFFieldDefinition],
        *,
        check_field_order: bool,
    ) -> dict[str, int]:
        left_map = {field.name: field for field in fields1}
        right_map = {field.name: field for field in fields2}
        left_names = [field.name for field in fields1]
        right_names = [field.name for field in fields2]

        common = [name for name in left_names if name in right_map]
        type_mismatches_count = sum(
            1
            for name in common
            if (
                left_map[name].type != right_map[name].type
                or left_map[name].length != right_map[name].length
                or left_map[name].decimal_count != right_map[name].decimal_count
            )
        )

        field_order_mismatches_count = 0
        if check_field_order:
            max_len = max(len(left_names), len(right_names))
            field_order_mismatches_count = sum(
                1
                for index in range(max_len)
                if (left_names[index] if index < len(left_names) else None)
                != (right_names[index] if index < len(right_names) else None)
            )

        return {
            "common_field_count": len(common),
            "missing_fields_count": sum(1 for name in left_names if name not in right_map),
            "extra_fields_count": sum(1 for name in right_names if name not in left_map),
            "type_mismatches_count": type_mismatches_count,
            "field_order_mismatches_count": field_order_mismatches_count,
        }

    def _build_category(self, code: str, label: str, count: int) -> ComparisonCategoryItem:
        return ComparisonCategoryItem(
            code=code,
            label=label,
            count=count,
            status="attention" if count else "ok",
        )

    def _build_schema_preview(
        self,
        fields1: list[DBFFieldDefinition],
        fields2: list[DBFFieldDefinition],
        *,
        check_field_order: bool,
    ) -> dict[str, list[dict[str, object]]]:
        left_map = {field.name: field for field in fields1}
        right_map = {field.name: field for field in fields2}
        left_names = [field.name for field in fields1]
        right_names = [field.name for field in fields2]

        structure_rows: list[dict[str, object]] = []
        type_rows: list[dict[str, object]] = []
        order_rows: list[dict[str, object]] = []

        for name in left_names:
            if name not in right_map:
                structure_rows.append({"field": name, "issue": "missing_in_file2", "file": "file1"})
        for name in right_names:
            if name not in left_map:
                structure_rows.append({"field": name, "issue": "extra_in_file2", "file": "file2"})
        for name in [name for name in left_names if name in right_map]:
            if (
                left_map[name].type != right_map[name].type
                or left_map[name].length != right_map[name].length
                or left_map[name].decimal_count != right_map[name].decimal_count
            ):
                type_rows.append(
                    {
                        "field": name,
                        "file1_type": self._format_type(left_map[name]),
                        "file2_type": self._format_type(right_map[name]),
                    }
                )

        if check_field_order:
            max_len = max(len(left_names), len(right_names))
            for index in range(max_len):
                file1_field = left_names[index] if index < len(left_names) else None
                file2_field = right_names[index] if index < len(right_names) else None
                if file1_field != file2_field:
                    order_rows.append(
                        {
                            "position": index + 1,
                            "file1_field": file1_field or "",
                            "file2_field": file2_field or "",
                        }
                    )

        return {
            "STRUCTURE": structure_rows,
            "FIELD_ORDER": order_rows,
            "TYPES": type_rows,
        }

    def _group_rows(
        self, records: list[dict[str, object]], key_fields: list[str]
    ) -> dict[tuple[object, ...], list[dict[str, object]]]:
        grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
        for record in records:
            key = tuple(record.get(field) for field in key_fields)
            grouped.setdefault(key, []).append(record)
        return grouped

    def _build_duplicates_preview(
        self, counts1: Counter[tuple[object, ...]], counts2: Counter[tuple[object, ...]]
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for file_name, counts in (("file1", counts1), ("file2", counts2)):
            for key, count in counts.items():
                if count > 1:
                    rows.append({"file": file_name, "key": self._format_key(key), "occurrences": count})
        return rows

    def _build_reconciliation_preview(
        self, keys1: set[tuple[object, ...]], keys2: set[tuple[object, ...]]
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for key in sorted(keys1 - keys2, key=str):
            rows.append({"issue": "missing_in_file2", "key": self._format_key(key)})
        for key in sorted(keys2 - keys1, key=str):
            rows.append({"issue": "extra_in_file2", "key": self._format_key(key)})
        return rows

    def _build_details_preview(
        self,
        *,
        key_rows_1: dict[tuple[object, ...], list[dict[str, object]]],
        key_rows_2: dict[tuple[object, ...], list[dict[str, object]]],
        common_fields: list[str],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for key in sorted(set(key_rows_1.keys()) & set(key_rows_2.keys()), key=str):
            record1 = key_rows_1[key][0]
            record2 = key_rows_2[key][0]
            for field in common_fields:
                value1 = record1.get(field)
                value2 = record2.get(field)
                if value1 != value2:
                    rows.append(
                        {
                            "key": self._format_key(key),
                            "field": field,
                            "file1_value": self._stringify_value(value1),
                            "file2_value": self._stringify_value(value2),
                        }
                    )
        return rows

    def _format_key(self, key: tuple[object, ...]) -> str:
        return " | ".join(self._stringify_value(part) for part in key)

    def _stringify_value(self, value: object) -> str:
        if value is None:
            return "<NULL>"
        if isinstance(value, str):
            return value
        return str(value)

    def _format_type(self, field: DBFFieldDefinition) -> str:
        return f"{field.type}({field.length},{field.decimal_count})"
