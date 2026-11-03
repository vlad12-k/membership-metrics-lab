# G3 Checkpoint — Analytics Engineering

**Recorded:** 2026-10-28 (UTC)  
**Gate:** G3 — Analytics engineering accepted: **PASSED locally**

## Implemented

- PostgreSQL 18.6 ARM64 container with persistent project-local volume and `127.0.0.1:54329` host binding. `.env` is local, generated randomly and ignored by Git; no password is recorded in source or logs.
- dbt Core 1.12.6 + dbt-postgres 1.11.0 project, local env-var profile, explicit `raw`, `staging`, `intermediate` and `marts` schemas, YAML seed types and a custom schema-name macro.
- Nine synthetic seeds (eight source CSVs plus simulation-period control); nine staging views; two event/redemption intermediate models plus pair-period eligibility; six dimensional/fact models; four reporting marts.
- Model/column documentation, executable seed/model tests, temporal integrity assertions, KPI bounds and source reconciliation tests, one dbt unit test for both partial calendar-month edges, and a durable Mermaid lineage diagram.
- Pair-level offer-rate denominators, distinct partner denominators, one-row-per-event redemption fact, separate point-in-time snapshots and period-flow measures, and complete-month cohort-retention handling.

## Runtime and tests — actual outputs

- `docker-compose version` → **5.1.4**. The host has no `docker compose` plugin command; the standalone `docker-compose` CLI was used. Existing unrelated containers/networks were left untouched.
- `docker-compose up -d --wait --wait-timeout 90 warehouse` → project warehouse **healthy**. Container reported PostgreSQL **18.6**, Linux **aarch64**; image digest `sha256:979bccfde35445db618c65107d27d08c6c21339d8dc3ad4c830c6633947be0e4`.
- `dbt debug` → all checks passed; connection test OK.
- `dbt ls --resource-type seed` → nine expected resources.
- `dbt seed` → all nine seeds loaded: 10,000 members; 11,748 status rows; 8 categories; 250 partners; 1,000 offers; 50,000 eligibility rows; 5,013 redemptions; 14,506 member events; one simulation-period row.
- `dbt parse` and `dbt compile` → passed. `dbt docs generate` → catalog written to ignored `dbt/target/catalog.json`.
- Two consecutive full `dbt build` executions completed in **26.92 s** and **26.89 s**. Each result set: **21 models successful, 9 seeds successful, 120 data tests passed, 1 unit test passed; 151 total resource results**. These are single-host local timings, not production or capacity benchmarks.
- All nine mart relations matched row-for-row fingerprints across the repeated builds: `dim_date` 549; `dim_members` 10,000; `dim_offers` 1,000; `dim_partners` 250; `fct_redemptions` 5,013; `mart_member_engagement` 95,148; `mart_partner_performance` 2,279; `mart_cohort_retention` 171; `mart_executive_kpis` 18.
- Source reconciliation passed for monthly redemptions, monthly active members, registered/eligible/30-day-active members and active partners. Bounds tests passed for rates/populations, partner engagement and cohort retention. A partial-month unit test passed.

## Debugging evidence

The first DBT build exposed an invalid `dim_date` join key; after correction, a direct source comparison found that the rolling-30-day KPI omitted eligible activity from the prior month. The engagement model was corrected to include the full inclusive 30-date window while keeping monthly activity scoped to its calendar month; the independent source reconciliation then passed. A cohort test also caught a denominator incorrectly calculated only in age-zero rows; cohort size is now computed separately and reused at each month age. The final two complete builds passed after these fixes.

PostgreSQL 18's image changed its expected volume mount to `/var/lib/postgresql`. The first mount attempt was stopped after the entrypoint rejected the legacy location; Compose now mounts the project volume at the documented parent path. No unrelated volume was removed.

## Evidence files

- [`../architecture/dbt-model-plan.md`](../architecture/dbt-model-plan.md)
- [`../architecture/dbt-lineage.md`](../architecture/dbt-lineage.md)
- `dbt/dbt_project.yml`, `dbt/profiles/profiles.yml`, `compose.yaml`
- `dbt/models/staging/`, `dbt/models/intermediate/`, `dbt/models/marts/`, `dbt/tests/`
- `dbt/target/manifest.json`, `dbt/target/catalog.json` (generated and ignored, not committed)
- `dbt/target/run_results.json` (generated and ignored)

## Residual risks / next gate

G3 is a local technical gate, not a production-readiness or stakeholder sign-off. Python negative fixtures prove the row-level validator detects specified source defects; the active clean-dataset dbt build is guarded by tests, but an end-to-end malformed CSV-to-dbt fixture has not been run. Lightdash has not been installed or connected; no dashboard, screenshots or external user experience are claimed. Proceed to G4 only after verifying official local Lightdash setup and warehouse networking.
