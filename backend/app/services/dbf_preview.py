from pathlib import Path

from dbfread import DBF


class DBFPreviewError(Exception):
    """Raised when DBF preview extraction fails."""


class DBFPreviewService:
    encodings = ("cp866", "cp1251")

    def read_fields(self, path: Path) -> tuple[list[str], str | None]:
        last_error: Exception | None = None

        for encoding in self.encodings:
            try:
                table = DBF(
                    str(path),
                    encoding=encoding,
                    char_decode_errors="strict",
                    ignore_missing_memofile=True,
                    load=False,
                    raw=False,
                )
                return list(table.field_names), encoding
            except Exception as exc:  # noqa: BLE001
                last_error = exc

        raise DBFPreviewError(f"Unable to read DBF structure from {path.name}: {last_error}")
