from __future__ import annotations

import csv
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from membership_metrics.generate import generate_dataset
from membership_metrics.validate import safe_rate, validate_dataset


@pytest.fixture
def clean_dataset(tmp_path: Path) -> Path:
    path = tmp_path / "clean"
    generate_dataset(
        path,
        seed=7,
        start_date="2025-01-01",
        end_date="2025-03-31",
        member_count=30,
        partner_count=4,
        offer_count=8,
        eligible_members_per_offer=20,
    )
    return path


def _mutate_csv(path: Path, table: str, mutate: Callable[[list[dict[str, str]]], None]) -> None:
    csv_path = path / f"{table}.csv"
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    mutate(rows)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _mutant(clean_dataset: Path, target: Path, table: str, mutate: Callable) -> Path:
    shutil.copytree(clean_dataset, target)
    _mutate_csv(target, table, mutate)
    return target


def test_clean_synthetic_dataset_passes_all_validations(clean_dataset: Path) -> None:
    report = validate_dataset(clean_dataset)

    assert report.valid
    assert report.issues == ()


def test_simulation_period_must_match_provenance(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "provenance-mismatch",
        "simulation_period",
        lambda rows: rows[0].update(seed="999"),
    )

    assert "PROVENANCE_MISMATCH" in validate_dataset(invalid).issue_codes


def test_required_null_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "null-required",
        "members",
        lambda rows: rows[0].update(registration_date=""),
    )

    assert "REQUIRED_NULL" in validate_dataset(invalid).issue_codes


def test_duplicate_event_identifier_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    def duplicate_first(rows: list[dict[str, str]]) -> None:
        assert rows
        rows.append(rows[0].copy())

    invalid = _mutant(clean_dataset, tmp_path / "duplicate-event", "member_events", duplicate_first)

    assert "DUPLICATE_KEY" in validate_dataset(invalid).issue_codes


def test_invalid_foreign_key_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "invalid-fk",
        "member_events",
        lambda rows: rows[0].update(member_id="MEM999999"),
    )

    assert "FOREIGN_KEY" in validate_dataset(invalid).issue_codes


def test_unexpected_membership_status_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "unexpected-status",
        "membership_status_history",
        lambda rows: rows[0].update(status="paused-unexpected"),
    )

    assert "UNEXPECTED_VALUE" in validate_dataset(invalid).issue_codes


def test_impossible_activity_timestamp_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "impossible-time",
        "member_events",
        lambda rows: rows[0].update(event_at="2099-01-01T00:00:00Z"),
    )

    assert "EVENT_OUTSIDE_SIMULATION_RANGE" in validate_dataset(invalid).issue_codes


def test_redemption_outside_offer_period_is_detected(clean_dataset: Path, tmp_path: Path) -> None:
    invalid = _mutant(
        clean_dataset,
        tmp_path / "out-of-window",
        "redemptions",
        lambda rows: rows[0].update(redeemed_at="2099-01-01T00:00:00Z"),
    )

    assert "REDEMPTION_OUTSIDE_OFFER" in validate_dataset(invalid).issue_codes


def test_zero_denominator_is_undefined_not_zero_percent() -> None:
    assert safe_rate(0, 0) is None
    with pytest.raises(ValueError, match="numerator cannot exceed"):
        safe_rate(4, 0)


def test_rate_rejects_numerator_greater_than_denominator() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        safe_rate(4, 3)
