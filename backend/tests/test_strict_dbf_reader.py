from datetime import datetime
from pathlib import Path
from struct import pack

from app.services.strict_dbf_reader import StrictDBFReader


def write_dbf(path: Path, fields: list[tuple[str, int]], rows: list[tuple[str, ...]], encoding: str = "cp866") -> None:
    now = datetime.now()
    num_records = len(rows)
    record_length = 1 + sum(length for _, length in fields)
    header_length = 32 + 32 * len(fields) + 1

    with path.open("wb") as handle:
        handle.write(
            pack(
                "<BBBBIHH20x",
                0x03,
                now.year - 1900,
                now.month,
                now.day,
                num_records,
                header_length,
                record_length,
            )
        )
        for name, length in fields:
            name_bytes = name.encode("ascii")[:11].ljust(11, b"\x00")
            handle.write(pack("<11sc4xBB14x", name_bytes, b"C", length, 0))
        handle.write(b"\r")

        for row in rows:
            handle.write(b" ")
            for (_, length), value in zip(fields, row):
                encoded = value.encode(encoding, errors="strict")[:length]
                handle.write(encoded.ljust(length, b" "))
        handle.write(b"\x1a")


def test_strict_dbf_reader_preserves_whitespace(tmp_path: Path) -> None:
    source = tmp_path / "sample.dbf"
    write_dbf(source, [("ID", 10), ("VALUE", 10)], [("1", "A "), ("2", "B\t")])

    table = StrictDBFReader().read_table(source)

    assert table.records[0]["VALUE"].startswith("A ")
    assert table.records[0]["VALUE"].endswith(" " * 8)
    assert "\t" in table.records[1]["VALUE"]
