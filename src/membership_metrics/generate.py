from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
CATEGORIES = (
    "Travel",
    "Food and drink",
    "Retail",
    "Home and garden",
    "Health and wellbeing",
    "Entertainment",
    "Automotive",
    "Services",
)
EVENT_TYPES = ("offer_view", "offer_save", "partner_view")
TABLES: dict[str, tuple[str, ...]] = {
    "members": ("member_id", "registration_date"),
    "membership_status_history": (
        "member_id",
        "status",
        "effective_start_date",
        "effective_end_date",
    ),
    "partner_categories": ("category_id", "category_name"),
    "partners": ("partner_id", "category_id", "active_from", "active_to"),
    "offers": ("offer_id", "partner_id", "offer_title", "valid_from", "valid_to"),
    "offer_eligibility": ("member_id", "offer_id", "eligible_from", "eligible_to"),
    "redemptions": ("redemption_id", "member_id", "offer_id", "redeemed_at", "status"),
    "member_events": ("event_id", "member_id", "event_type", "event_at"),
    "simulation_period": (
        "period_id",
        "simulation_start_date",
        "simulation_end_date_inclusive",
        "seed",
        "schema_version",
    ),
}


def _as_date(value: date | str, *, field: str) -> date:
    if isinstance(value, datetime):
        raise TypeError(f"{field} must be a date or ISO date string, not datetime")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO date (YYYY-MM-DD)") from exc


def _random_date(rng: random.Random, start: date, end_exclusive: date) -> date:
    span_days = (end_exclusive - start).days
    if span_days < 1:
        raise ValueError("date interval must contain at least one calendar day")
    return start + timedelta(days=rng.randrange(span_days))


def _month_starts(start: date, end: date) -> list[date]:
    current = start.replace(day=1)
    last = end.replace(day=1)
    months = []
    while current <= last:
        months.append(current)
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate_dataset(
    output_dir: Path | str,
    *,
    seed: int = 42,
    start_date: date | str = "2024-07-01",
    end_date: date | str = "2025-12-31",
    member_count: int = 10_000,
    partner_count: int = 250,
    offer_count: int = 1_000,
    eligible_members_per_offer: int = 50,
) -> dict[str, Any]:
    """Generate clean, deterministic synthetic membership source files.

    The inclusive simulation end date is converted to an exclusive boundary for
    business validity intervals. Existing non-empty directories are rejected
    to avoid overwriting files unrelated to this generator.
    """
    start = _as_date(start_date, field="start_date")
    end = _as_date(end_date, field="end_date")
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    for name, value in (
        ("member_count", member_count),
        ("partner_count", partner_count),
        ("offer_count", offer_count),
        ("eligible_members_per_offer", eligible_members_per_offer),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"refusing to write into non-empty output directory: {destination}; "
            "choose a new directory"
        )
    destination.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    horizon_end = end + timedelta(days=1)
    start_text = start.isoformat()
    end_text = end.isoformat()

    categories = [
        {"category_id": f"CAT{index:03d}", "category_name": name}
        for index, name in enumerate(CATEGORIES, start=1)
    ]

    members: list[dict[str, str]] = []
    status_history: list[dict[str, str | None]] = []
    member_lifecycles: dict[str, tuple[date, date | None]] = {}
    for index in range(1, member_count + 1):
        member_id = f"MEM{index:06d}"
        registered = _random_date(rng, start, horizon_end)
        churn_date: date | None = None
        if (horizon_end - registered).days > 30 and rng.random() < 0.18:
            churn_date = registered + timedelta(
                days=rng.randint(30, (horizon_end - registered).days)
            )
        members.append({"member_id": member_id, "registration_date": registered.isoformat()})
        status_history.append(
            {
                "member_id": member_id,
                "status": "active",
                "effective_start_date": registered.isoformat(),
                "effective_end_date": churn_date.isoformat() if churn_date else None,
            }
        )
        if churn_date:
            status_history.append(
                {
                    "member_id": member_id,
                    "status": "inactive",
                    "effective_start_date": churn_date.isoformat(),
                    "effective_end_date": None,
                }
            )
        member_lifecycles[member_id] = (registered, churn_date)

    partners: list[dict[str, str | None]] = []
    partner_lifecycles: dict[str, tuple[date, date | None]] = {}
    for index in range(1, partner_count + 1):
        partner_id = f"PAR{index:04d}"
        active_from = _random_date(rng, start, horizon_end)
        active_to = None
        if (horizon_end - active_from).days > 30 and rng.random() < 0.12:
            active_to = active_from + timedelta(
                days=rng.randint(30, (horizon_end - active_from).days)
            )
        category_id = f"CAT{rng.randint(1, len(CATEGORIES)):03d}"
        partners.append(
            {
                "partner_id": partner_id,
                "category_id": category_id,
                "active_from": active_from.isoformat(),
                "active_to": active_to.isoformat() if active_to else None,
            }
        )
        partner_lifecycles[partner_id] = (active_from, active_to)

    offers: list[dict[str, str]] = []
    offer_lifecycles: dict[str, tuple[str, date, date]] = {}
    partner_ids = [f"PAR{index:04d}" for index in range(1, partner_count + 1)]
    for index in range(1, offer_count + 1):
        offer_id = f"OFF{index:05d}"
        partner_id = rng.choice(partner_ids)
        partner_start, partner_end = partner_lifecycles[partner_id]
        earliest = max(start, partner_start)
        latest_exclusive = min(horizon_end, partner_end or horizon_end)
        if (latest_exclusive - earliest).days < 1:
            earliest = start
            latest_exclusive = horizon_end
        valid_from = _random_date(rng, earliest, latest_exclusive)
        max_end = min(latest_exclusive, valid_from + timedelta(days=rng.randint(14, 90)))
        valid_to = max_end if max_end > valid_from else valid_from + timedelta(days=1)
        offers.append(
            {
                "offer_id": offer_id,
                "partner_id": partner_id,
                "offer_title": f"Synthetic offer {index:04d}",
                "valid_from": valid_from.isoformat(),
                "valid_to": valid_to.isoformat(),
            }
        )
        offer_lifecycles[offer_id] = (partner_id, valid_from, valid_to)

    eligibility: list[dict[str, str]] = []
    eligible_pairs: list[tuple[str, str, date, date]] = []
    for offer_id, (_, offer_start, offer_end) in offer_lifecycles.items():
        candidates: list[tuple[str, date, date]] = []
        for member_id, (registered, inactive_from) in member_lifecycles.items():
            eligible_from = max(offer_start, registered)
            eligible_to = min(offer_end, inactive_from or horizon_end)
            if eligible_from < eligible_to:
                candidates.append((member_id, eligible_from, eligible_to))
        selected = rng.sample(candidates, k=min(eligible_members_per_offer, len(candidates)))
        for member_id, eligible_from, eligible_to in selected:
            eligibility.append(
                {
                    "member_id": member_id,
                    "offer_id": offer_id,
                    "eligible_from": eligible_from.isoformat(),
                    "eligible_to": eligible_to.isoformat(),
                }
            )
            eligible_pairs.append((member_id, offer_id, eligible_from, eligible_to))

    redemptions: list[dict[str, str]] = []
    redemption_number = 0
    for member_id, offer_id, eligible_from, eligible_to in eligible_pairs:
        if rng.random() >= 0.09:
            continue
        redemption_count = 1 + int((eligible_to - eligible_from).days > 1 and rng.random() < 0.12)
        for _ in range(redemption_count):
            redeemed_date = _random_date(rng, eligible_from, eligible_to)
            redeemed_at = datetime.combine(
                redeemed_date,
                datetime.min.time().replace(
                    hour=rng.randrange(24), minute=rng.randrange(60), second=rng.randrange(60)
                ),
                tzinfo=UTC,
            )
            redemption_number += 1
            redemptions.append(
                {
                    "redemption_id": f"RDM{redemption_number:08d}",
                    "member_id": member_id,
                    "offer_id": offer_id,
                    "redeemed_at": redeemed_at.isoformat().replace("+00:00", "Z"),
                    "status": "complete",
                }
            )

    events: list[dict[str, str]] = []
    event_number = 0
    for member_id, (registered, inactive_from) in member_lifecycles.items():
        active_end = min(horizon_end, inactive_from or horizon_end)
        for month_start in _month_starts(registered, end):
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            lower = max(registered, month_start)
            upper = min(active_end, month_end, horizon_end)
            if lower >= upper:
                continue
            seasonal_factor = 1.5 if month_start.month in (6, 11, 12) else 1.0
            if rng.random() >= min(0.24, 0.12 * seasonal_factor):
                continue
            activity_count = 1 + int(rng.random() < 0.18)
            for _ in range(activity_count):
                event_date = _random_date(rng, lower, upper)
                event_at = datetime.combine(
                    event_date,
                    datetime.min.time().replace(
                        hour=rng.randrange(24), minute=rng.randrange(60), second=rng.randrange(60)
                    ),
                    tzinfo=UTC,
                )
                event_number += 1
                events.append(
                    {
                        "event_id": f"EVT{event_number:09d}",
                        "member_id": member_id,
                        "event_type": rng.choice(EVENT_TYPES),
                        "event_at": event_at.isoformat().replace("+00:00", "Z"),
                    }
                )

    tables: dict[str, list[dict[str, Any]]] = {
        "members": members,
        "membership_status_history": status_history,
        "partner_categories": categories,
        "partners": partners,
        "offers": offers,
        "offer_eligibility": eligibility,
        "redemptions": redemptions,
        "member_events": events,
        "simulation_period": [
            {
                "period_id": "SIM0001",
                "simulation_start_date": start_text,
                "simulation_end_date_inclusive": end_text,
                "seed": seed,
                "schema_version": SCHEMA_VERSION,
            }
        ],
    }
    counts = Counter({name: len(rows) for name, rows in tables.items()})
    for name, rows in tables.items():
        _write_csv(destination / f"{name}.csv", TABLES[name], rows)

    provenance = {
        "schema_version": SCHEMA_VERSION,
        "generator": "membership_metrics.generate",
        "seed": seed,
        "simulation_start_date": start_text,
        "simulation_end_date_inclusive": end_text,
        "record_counts": dict(sorted(counts.items())),
        "synthetic_data_notice": "All identifiers, entities, events and dates are synthetic.",
    }
    (destination / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic member data")
    parser.add_argument("--output", type=Path, default=Path("data/generated/dbt-seeds"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-date", default="2024-07-01")
    parser.add_argument("--end-date", default="2025-12-31")
    parser.add_argument("--members", type=int, default=10_000)
    parser.add_argument("--partners", type=int, default=250)
    parser.add_argument("--offers", type=int, default=1_000)
    parser.add_argument("--eligible-members-per-offer", type=int, default=50)
    args = parser.parse_args()
    summary = generate_dataset(
        args.output,
        seed=args.seed,
        start_date=args.start_date,
        end_date=args.end_date,
        member_count=args.members,
        partner_count=args.partners,
        offer_count=args.offers,
        eligible_members_per_offer=args.eligible_members_per_offer,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
