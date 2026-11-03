# Synthetic Data Contract

**Schema version:** 1.0.0  
**Generator:** `src/membership_metrics/generate.py`  
**Default interval:** 2024-07-01 through 2025-12-31 inclusive (18 calendar months)  
**Default seed:** 42  
**Data status:** Synthetic only; no real persons, customer records, business partners or employer systems.

## File schemas and grains

All outputs are UTF-8 CSV with a header and deterministic row order. Dates use ISO `YYYY-MM-DD`; timestamps are ISO UTC ending in `Z`; empty optional interval ends mean open-ended. Source IDs are pseudonymous, deterministic synthetic keys.

| File | Grain / primary key | Fields and rules |
|---|---|---|
| `members.csv` | One member; `member_id` | `member_id` synthetic `MEM######`; `registration_date` inclusive simulation date. |
| `membership_status_history.csv` | One status interval per member/start; `(member_id, effective_start_date)` | `status` is `active` or `inactive`; half-open interval `[effective_start_date, effective_end_date)`; blank end means open. A member may have an active interval followed by an inactive interval; intervals do not overlap. |
| `partner_categories.csv` | One category; `category_id` | Synthetic `CAT###`; `category_name` from fixed deterministic eight-category list. |
| `partners.csv` | One partner; `partner_id` | Synthetic `PAR####`; `category_id` FK; `active_from` inclusive and optional `active_to` exclusive. One category per partner in v1. |
| `offers.csv` | One offer; `offer_id` | Synthetic `OFF#####`; `partner_id` FK; descriptive synthetic title; `[valid_from, valid_to)` with positive duration and validity within partner active period where generated. |
| `offer_eligibility.csv` | One member-offer eligibility interval; `(member_id, offer_id)` | Member and offer FKs; `[eligible_from, eligible_to)` is positive-duration and contained within offer validity and an active membership interval. |
| `redemptions.csv` | One source redemption event; `redemption_id` | Synthetic sequential `RDM########`; member/offer FKs; timezone-aware `redeemed_at`; status is `complete` in the clean generator. Repeated events have separate IDs. |
| `member_events.csv` | One source activity event; `event_id` | Synthetic sequential `EVT#########`; member FK; `event_type` allowlist: `offer_view`, `offer_save`, `partner_view`; timezone-aware `event_at`; clean events occur during active membership and simulation dates. |
| `simulation_period.csv` | One control row; `period_id` | Inclusive start/end dates, random seed and schema version. dbt consumes this control row to build the exact date spine; it must match `provenance.json`. |

`dim_date` is a dbt model generated from the control row's date range, not a generator CSV. Table/model grains are also recorded in [`../business/requirements.md`](../business/requirements.md).

## Generation and provenance

The generator uses a local `random.Random(seed)` instance and never mutates process-global random state. It emits eight source CSVs, one simulation-control CSV and `provenance.json`. Provenance records schema version, generator name, seed, inclusive date range, per-file row counts and an explicit synthetic-data notice. It intentionally omits wall-clock generation time so equivalent runs can produce byte-identical files.

The generator refuses to write into a non-empty destination directory. This prevents accidental overwrite of unrelated local files; choose a fresh output directory for a new run. Generated production-like data defaults to `data/generated/dbt-seeds/`, which is ignored by Git and configured as dbt's seed path.

## Clean versus negative test data

- Clean generated output must pass `membership-metrics-validate`.
- Negative tests create isolated copies under pytest's temporary directory and mutate one property per test. They never modify `data/generated/` and do not mix corrupt examples into clean source files.
- Negative cases currently cover required NULLs, duplicate event IDs, invalid foreign keys, unknown membership statuses, impossible timestamps outside the declared simulation range, redemptions outside offer validity and zero-denominator KPI behavior.
- Each negative test asserts a specific validation issue code. Passing that test means the defect was detected, not that an invalid dataset is acceptable.

## Simplifications and limitations

This synthetic schema intentionally omits personally identifying information, actual financial values, payment/settlement, reversals from the clean source, offer impressions/exposure, multi-category partners, multiple simultaneous membership types and real-world source-system provenance. The generated event and redemption frequencies are test-design choices, not estimates of actual member behavior.
