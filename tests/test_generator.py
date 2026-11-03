from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from membership_metrics.generate import generate_dataset


def _checksums(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
        if path.is_file()
    }


def test_generation_is_byte_deterministic_for_the_same_seed(tmp_path: Path) -> None:
    options = {
        "seed": 7,
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
        "member_count": 30,
        "partner_count": 4,
        "offer_count": 8,
    }

    first = tmp_path / "first"
    second = tmp_path / "second"
    first_summary = generate_dataset(first, **options)
    second_summary = generate_dataset(second, **options)

    assert first_summary == second_summary
    assert _checksums(first) == _checksums(second)
    assert first_summary["seed"] == 7
    assert first_summary["record_counts"]["members"] == 30
    assert {"members.csv", "redemptions.csv", "member_events.csv"}.issubset(
        {path.name for path in first.iterdir()}
    )


def test_generator_refuses_to_overwrite_non_empty_output(tmp_path: Path) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("unrelated local data", encoding="utf-8")

    with pytest.raises(FileExistsError, match="non-empty output directory"):
        generate_dataset(destination, member_count=2, partner_count=1, offer_count=1)

    assert marker.read_text(encoding="utf-8") == "unrelated local data"


def test_generation_persists_the_declared_simulation_period(tmp_path: Path) -> None:
    output = tmp_path / "period"
    generate_dataset(
        output,
        seed=9,
        start_date="2025-02-01",
        end_date="2025-02-28",
        member_count=2,
        partner_count=1,
        offer_count=1,
    )

    with (output / "simulation_period.csv").open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    assert row["simulation_start_date"] == "2025-02-01"
    assert row["simulation_end_date_inclusive"] == "2025-02-28"
    assert row["seed"] == "9"
