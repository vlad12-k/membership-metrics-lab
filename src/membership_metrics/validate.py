from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from membership_metrics.generate import TABLES

OPTIONAL_COLUMNS = {
    "membership_status_history": {"effective_end_date"},
    "partners": {"active_to"},
}
PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "members": ("member_id",),
    "membership_status_history": ("member_id", "effective_start_date"),
    "partner_categories": ("category_id",),
    "partners": ("partner_id",),
    "offers": ("offer_id",),
    "offer_eligibility": ("member_id", "offer_id"),
    "redemptions": ("redemption_id",),
    "member_events": ("event_id",),
    "simulation_period": ("period_id",),
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    table: str
    row_number: int | None
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    @property
    def issue_codes(self) -> frozenset[str]:
        return frozenset(issue.code for issue in self.issues)

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "code": issue.code,
                    "table": issue.table,
                    "row_number": issue.row_number,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def safe_rate(numerator: int, denominator: int) -> float | None:
    """Return an undefined rate for a 0/0 population and reject invalid counts."""
    if numerator < 0 or denominator < 0:
        raise ValueError("rate counts must be non-negative")
    if numerator > denominator:
        raise ValueError("rate numerator cannot exceed denominator")
    if denominator == 0:
        return None
    return numerator / denominator


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _interval_contains(start: date, end: date | None, point: date) -> bool:
    return start <= point and (end is None or point < end)


def _interval_covers(start: date, end: date, outer_start: date, outer_end: date | None) -> bool:
    return outer_start <= start and (outer_end is None or end <= outer_end)


def validate_dataset(dataset_dir: Path | str) -> ValidationReport:
    """Validate synthetic source CSVs and their keys, references and temporal rules."""
    directory = Path(dataset_dir)
    issues: list[ValidationIssue] = []
    tables: dict[str, list[dict[str, str | None]]] = {}

    def add(code: str, table: str, row_number: int | None, message: str) -> None:
        issues.append(ValidationIssue(code, table, row_number, message))

    for table, columns in TABLES.items():
        path = directory / f"{table}.csv"
        if not path.is_file():
            add("MISSING_TABLE", table, None, f"required file not found: {path.name}")
            tables[table] = []
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            missing_columns = set(columns) - set(header)
            if missing_columns:
                add(
                    "SCHEMA_COLUMNS",
                    table,
                    1,
                    f"missing required columns: {', '.join(sorted(missing_columns))}",
                )
            rows = list(reader)
        tables[table] = rows
        required = set(columns) - OPTIONAL_COLUMNS.get(table, set())
        for row_number, row in enumerate(rows, start=2):
            for column in required:
                if not row.get(column):
                    add("REQUIRED_NULL", table, row_number, f"{column} must not be NULL or empty")

    for table, key_fields in PRIMARY_KEYS.items():
        seen: set[tuple[str, ...]] = set()
        for row_number, row in enumerate(tables[table], start=2):
            key = tuple(row.get(field) or "" for field in key_fields)
            if any(not part for part in key):
                continue
            if key in seen:
                add("DUPLICATE_KEY", table, row_number, f"duplicate key: {key}")
            seen.add(key)

    target_ids = {
        (table, key): {row.get(key) for row in tables[table] if row.get(key)}
        for table, key in (
            ("members", "member_id"),
            ("partner_categories", "category_id"),
            ("partners", "partner_id"),
            ("offers", "offer_id"),
        )
    }
    foreign_keys = (
        ("membership_status_history", "member_id", "members", "member_id"),
        ("partners", "category_id", "partner_categories", "category_id"),
        ("offers", "partner_id", "partners", "partner_id"),
        ("offer_eligibility", "member_id", "members", "member_id"),
        ("offer_eligibility", "offer_id", "offers", "offer_id"),
        ("redemptions", "member_id", "members", "member_id"),
        ("redemptions", "offer_id", "offers", "offer_id"),
        ("member_events", "member_id", "members", "member_id"),
    )
    for table, column, target_table, target_column in foreign_keys:
        valid_ids = target_ids[(target_table, target_column)]
        for row_number, row in enumerate(tables[table], start=2):
            value = row.get(column)
            if value and value not in valid_ids:
                add(
                    "FOREIGN_KEY",
                    table,
                    row_number,
                    f"{column}={value!r} does not exist in {target_table}.{target_column}",
                )

    status_intervals: dict[str, list[tuple[str, date, date | None, int]]] = defaultdict(list)
    for row_number, row in enumerate(tables["membership_status_history"], start=2):
        member_id = row.get("member_id") or ""
        status = row.get("status") or ""
        if status not in {"active", "inactive"}:
            add(
                "UNEXPECTED_VALUE",
                "membership_status_history",
                row_number,
                f"unexpected status {status!r}",
            )
        start = _parse_date(row.get("effective_start_date"))
        end = _parse_date(row.get("effective_end_date"))
        if start is None:
            add(
                "INVALID_DATE",
                "membership_status_history",
                row_number,
                "invalid effective_start_date",
            )
            continue
        if row.get("effective_end_date") and end is None:
            add(
                "INVALID_DATE",
                "membership_status_history",
                row_number,
                "invalid effective_end_date",
            )
        if end is not None and start >= end:
            add(
                "INVALID_INTERVAL",
                "membership_status_history",
                row_number,
                "status interval must have positive duration",
            )
        status_intervals[member_id].append((status, start, end, row_number))
    for member_id, intervals in status_intervals.items():
        ordered = sorted(intervals, key=lambda item: item[1])
        for previous, current in itertools.pairwise(ordered):
            if previous[2] is None or current[1] < previous[2]:
                add(
                    "OVERLAPPING_INTERVAL",
                    "membership_status_history",
                    current[3],
                    f"overlapping status intervals for {member_id}",
                )

    offer_rows: dict[str, tuple[date, date, int]] = {}
    for row_number, row in enumerate(tables["offers"], start=2):
        start = _parse_date(row.get("valid_from"))
        end = _parse_date(row.get("valid_to"))
        if start is None or end is None:
            add("INVALID_DATE", "offers", row_number, "valid_from and valid_to must be ISO dates")
        elif start >= end:
            add(
                "INVALID_INTERVAL",
                "offers",
                row_number,
                "offer validity must have positive duration",
            )
        else:
            offer_rows[row.get("offer_id") or ""] = (start, end, row_number)

    eligibility_rows: dict[tuple[str, str], list[tuple[date, date, int]]] = defaultdict(list)
    for row_number, row in enumerate(tables["offer_eligibility"], start=2):
        member_id = row.get("member_id") or ""
        offer_id = row.get("offer_id") or ""
        start = _parse_date(row.get("eligible_from"))
        end = _parse_date(row.get("eligible_to"))
        if start is None or end is None:
            add(
                "INVALID_DATE",
                "offer_eligibility",
                row_number,
                "eligibility dates must be ISO dates",
            )
            continue
        if start >= end:
            add(
                "INVALID_INTERVAL",
                "offer_eligibility",
                row_number,
                "eligibility interval must have positive duration",
            )
            continue
        eligibility_rows[(member_id, offer_id)].append((start, end, row_number))
        offer = offer_rows.get(offer_id)
        if offer and (start < offer[0] or end > offer[1]):
            add(
                "ELIGIBILITY_OUTSIDE_OFFER",
                "offer_eligibility",
                row_number,
                "eligibility must be contained by offer validity",
            )
        active_ranges = [
            (status_start, status_end)
            for status, status_start, status_end, _ in status_intervals.get(member_id, [])
            if status == "active"
        ]
        if not any(
            _interval_covers(start, end, active_start, active_end)
            for active_start, active_end in active_ranges
        ):
            add(
                "ELIGIBILITY_OUTSIDE_MEMBERSHIP",
                "offer_eligibility",
                row_number,
                "eligibility must be within one active membership interval",
            )
    for pair, intervals in eligibility_rows.items():
        ordered = sorted(intervals, key=lambda item: item[0])
        for previous, current in itertools.pairwise(ordered):
            if current[0] < previous[1]:
                add(
                    "OVERLAPPING_INTERVAL",
                    "offer_eligibility",
                    current[2],
                    f"overlapping eligibility intervals for {pair}",
                )

    try:
        provenance = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
        simulation_start = _parse_date(provenance.get("simulation_start_date"))
        simulation_end = _parse_date(provenance.get("simulation_end_date_inclusive"))
        if simulation_start is None or simulation_end is None or simulation_start > simulation_end:
            raise ValueError("invalid simulation dates")
        period_rows = tables["simulation_period"]
        if len(period_rows) != 1:
            add(
                "INVALID_SIMULATION_PERIOD",
                "simulation_period",
                None,
                "simulation_period.csv must contain exactly one control row",
            )
        elif any(
            period_rows[0].get(key) != str(provenance.get(value))
            for key, value in (
                ("simulation_start_date", "simulation_start_date"),
                ("simulation_end_date_inclusive", "simulation_end_date_inclusive"),
                ("seed", "seed"),
                ("schema_version", "schema_version"),
            )
        ):
            add(
                "PROVENANCE_MISMATCH",
                "simulation_period",
                2,
                "control row does not match provenance.json",
            )
    except (OSError, json.JSONDecodeError, ValueError, AttributeError):
        simulation_start = None
        simulation_end = None
        add(
            "INVALID_PROVENANCE",
            "provenance",
            None,
            "provenance.json must contain a valid simulation date range",
        )

    for table, column in (("member_events", "event_at"), ("redemptions", "redeemed_at")):
        for row_number, row in enumerate(tables[table], start=2):
            timestamp = _parse_timestamp(row.get(column))
            if timestamp is None:
                add(
                    "INVALID_TIMESTAMP",
                    table,
                    row_number,
                    f"{column} must be a timezone-aware timestamp",
                )
                continue
            event_date = timestamp.date()
            if (
                simulation_start
                and simulation_end
                and not (simulation_start <= event_date <= simulation_end)
            ):
                code = (
                    "EVENT_OUTSIDE_SIMULATION_RANGE"
                    if table == "member_events"
                    else "REDEMPTION_OUTSIDE_SIMULATION_RANGE"
                )
                add(
                    code,
                    table,
                    row_number,
                    f"{column} falls outside the synthetic simulation period",
                )

            member_id = row.get("member_id") or ""
            if table == "member_events":
                if not any(
                    status == "active" and _interval_contains(start, end, event_date)
                    for status, start, end, _ in status_intervals.get(member_id, [])
                ):
                    add(
                        "EVENT_OUTSIDE_ACTIVE_MEMBERSHIP",
                        table,
                        row_number,
                        "activity requires active membership on event date",
                    )
                if row.get("event_type") not in {"offer_view", "offer_save", "partner_view"}:
                    add(
                        "UNEXPECTED_VALUE",
                        table,
                        row_number,
                        f"unexpected qualifying event type {row.get('event_type')!r}",
                    )
                continue

            redemption_status = row.get("status")
            if redemption_status not in {"complete", "cancelled", "reversed"}:
                add(
                    "UNEXPECTED_VALUE",
                    table,
                    row_number,
                    f"unexpected redemption status {redemption_status!r}",
                )
            if redemption_status != "complete":
                continue
            offer_id = row.get("offer_id") or ""
            offer = offer_rows.get(offer_id)
            if offer and not (offer[0] <= event_date < offer[1]):
                add(
                    "REDEMPTION_OUTSIDE_OFFER",
                    table,
                    row_number,
                    "completed redemption is outside offer validity",
                )
            member_active = any(
                status == "active" and _interval_contains(start, end, event_date)
                for status, start, end, _ in status_intervals.get(member_id, [])
            )
            if not member_active:
                add(
                    "REDEMPTION_OUTSIDE_ACTIVE_MEMBERSHIP",
                    table,
                    row_number,
                    "completed redemption requires active membership",
                )
            eligible = any(
                start <= event_date < end
                for start, end, _ in eligibility_rows.get((member_id, offer_id), [])
            )
            if not eligible:
                add(
                    "REDEMPTION_NOT_ELIGIBLE",
                    table,
                    row_number,
                    "completed redemption requires offer eligibility on redemption date",
                )

    return ValidationReport(tuple(issues))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated synthetic source CSVs")
    parser.add_argument("dataset", type=Path, nargs="?", default=Path("data/generated/dbt-seeds"))
    args = parser.parse_args()
    report = validate_dataset(args.dataset)
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    if not report.valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
