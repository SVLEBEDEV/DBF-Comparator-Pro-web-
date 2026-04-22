import json
from pathlib import Path
from typing import Any

import pytest

from app.services.comparison_engine import ComparisonEngine


CASES_ROOT = Path(__file__).resolve().parents[2] / "qa" / "test-data" / "manual-cases"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _load_case_specs() -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    specs: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for expected_path in sorted(CASES_ROOT.rglob("expected.json")):
        payload = json.loads(expected_path.read_text(encoding="utf-8"))
        for run in payload["runs"]:
            specs.append((expected_path.parent, payload, run))
    return specs


CASE_SPECS = _load_case_specs()


def _case_test_id(spec: tuple[Path, dict[str, Any], dict[str, Any]]) -> str:
    case_dir, payload, run = spec
    case_id = payload.get("case_id", case_dir.name)
    run_name = run.get("name", "default")
    return f"{case_id}:{run_name}"


def _assert_summary(actual_summary: dict[str, Any], expected_summary: dict[str, Any]) -> None:
    for key, expected_value in expected_summary.items():
        assert actual_summary[key] == expected_value


def _assert_preview(actual_preview: dict[str, Any], expected_preview: dict[str, Any]) -> None:
    normalized_preview = {section: _normalize(rows) for section, rows in actual_preview.items()}

    for section, expected_value in expected_preview.items():
        assert normalized_preview[section] == expected_value


@pytest.mark.parametrize("case_spec", CASE_SPECS, ids=_case_test_id)
def test_manual_regression_cases_from_expected_json(
    case_spec: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    case_dir, payload, run = case_spec
    params = run["params"]
    expected = run["expected"]

    result = ComparisonEngine().run(
        file1_path=str(case_dir / "left.dbf"),
        file2_path=str(case_dir / "right.dbf"),
        key1=params["key1"],
        key2=params.get("key2"),
        structure_only=params.get("structure_only", False),
        check_field_order=params.get("check_field_order", False),
    )

    _assert_summary(result.summary.model_dump(), expected.get("summary", {}))
    _assert_preview(result.preview, expected.get("preview", {}))

    if "notes" in payload:
        assert payload["notes"]
