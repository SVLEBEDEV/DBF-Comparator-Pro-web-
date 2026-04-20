from dataclasses import dataclass
from pathlib import Path

from dbfread import DBF


class StrictDBFReadError(Exception):
    """Raised when a DBF file cannot be read with supported encodings."""


@dataclass(slots=True)
class DBFFieldDefinition:
    name: str
    type: str
    length: int
    decimal_count: int


@dataclass(slots=True)
class DBFTableData:
    encoding: str
    fields: list[DBFFieldDefinition]
    records: list[dict[str, object]]


class StrictDBFReader:
    encodings = ("cp866", "cp1251")

    def read_table(self, path: str | Path) -> DBFTableData:
        source = Path(path)
        last_error: Exception | None = None

        for encoding in self.encodings:
            try:
                table = DBF(
                    str(source),
                    encoding=encoding,
                    char_decode_errors="strict",
                    ignore_missing_memofile=True,
                    load=False,
                    raw=True,
                )
                fields = [
                    DBFFieldDefinition(
                        name=field.name,
                        type=field.type,
                        length=field.length,
                        decimal_count=field.decimal_count,
                    )
                    for field in table.fields
                ]
                records = [self._normalize_record(dict(record), encoding=encoding) for record in table]
                return DBFTableData(encoding=encoding, fields=fields, records=records)
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        raise StrictDBFReadError(f"Unable to read DBF file {source.name}: {last_error}")

    def _normalize_record(self, record: dict[str, object], *, encoding: str) -> dict[str, object]:
        normalized: dict[str, object] = {}
        for key, value in record.items():
            if isinstance(value, bytes):
                normalized[key] = value.decode(encoding, errors="strict")
            else:
                normalized[key] = value
        return normalized
