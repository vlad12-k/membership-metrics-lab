# G2 Checkpoint — Synthetic Data Foundation

**Recorded:** 2026-10-28 (UTC)  
**Gate:** G2 — Data foundation accepted: **PASSED**

## Delivered

- Deterministic generator for eight source CSVs, one control CSV (`simulation_period.csv`) and `provenance.json`, with defaults seed 42, 2024-07-01 through 2025-12-31 inclusive, 10,000 members, 250 partners and 1,000 offers.
- Pseudonymous IDs and fictional categories/offers; no real or scraped records.
- Membership lifecycle and partner/offer validity intervals; sampled member-offer eligibility; repeated redemption events; seasonally weighted synthetic member activity.
- Validator for table/schema presence, required fields, unique/foreign keys, allowed statuses, interval boundaries, temporal eligibility, redemption validity and agreement between `simulation_period.csv` and provenance.
- Zero-denominator helper returns `None` for 0/0 and rejects invalid counts.
- Generator refuses to overwrite non-empty destinations.
- Grain, field, clean-data and negative-fixture rules in [`../data/synthetic-data-contract.md`](../data/synthetic-data-contract.md).

## Actual verification

- `TMPDIR=... .venv/bin/pytest tests/test_generator.py tests/test_validation.py -q` → **13 passed**; this includes clean-dataset validation and isolated controlled defects such as nulls, duplicate IDs, foreign-key defects, invalid statuses, out-of-period timestamps, out-of-offer redemptions, provenance mismatch and rate edge cases.
- `.venv/bin/ruff check src tests` → passed.
- `.venv/bin/ruff format --check src tests` → passed.
- `uv lock --check --python 3.12` → passed.
- The normal generator output at `data/generated/dbt-seeds/` was generated and validated: 10,000 members; 11,748 status intervals; 8 categories; 250 partners; 1,000 offers; 50,000 eligibility pairs; 5,013 redemptions; 14,506 member events; 1 control row; **0 validation issues**.
- Two full default runs in profile scratch produced **10 byte-identical files** and identical record summaries; validation reported **0 issues**. Combined generation time was **6.284 seconds**, output size **3,803,139 bytes** on this host. A single local measurement, not a performance guarantee.
- `data/generated/` is ignored by Git. CSV files are loaded locally through dbt seeds; none are committed.

## Files created/updated

- `src/membership_metrics/{__init__,generate,validate}.py`
- `tests/test_generator.py`, `tests/test_validation.py`
- `pyproject.toml`, `uv.lock`
- `docs/data/synthetic-data-contract.md`
- `docs/PROJECT_STATUS.md`, `README.md`, `docs/evidence/G2-checkpoint.md`
- Ignored local data: `data/generated/dbt-seeds/*.csv`, `data/generated/dbt-seeds/provenance.json`

## Limitations and next gate

The event frequencies/seasonality are scenario parameters and not empirical behavior. This gate establishes deterministic local data generation and detection of defined source defects; it does not establish database, dbt or BI correctness by itself. The PostgreSQL/dbt integration and model/KPI reconciliation are separately recorded in G3; Lightdash/dashboard acceptance remains G4.
