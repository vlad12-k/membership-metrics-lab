# G5 proposed initial-publication inventory

**Review state:** local release-candidate proposal only. Nothing has been staged, committed, pushed, or published. This list is the exact proposed first-commit allowlist; it does not authorize publication. Paths are repository-relative. Re-run the security scan and link/allowlist validation against this list immediately before any approved commit.

## Proposed files (79)

```text
.env.example
.github/workflows/ci.yml
.gitignore
README.md
compose.yaml
data/powerbi/snapshots/2026-10-28/kpi-reconciliation.csv
data/powerbi/snapshots/2026-10-28/manifest.json
data/powerbi/snapshots/2026-10-28/mart_cohort_retention.csv
data/powerbi/snapshots/2026-10-28/mart_executive_kpis.csv
data/powerbi/snapshots/2026-10-28/mart_member_engagement.csv
data/powerbi/snapshots/2026-10-28/mart_partner_performance.csv
dbt/dbt_project.yml
dbt/macros/generate_schema_name.sql
dbt/models/_models.yml
dbt/models/intermediate/int_eligible_member_offer_period.sql
dbt/models/intermediate/int_qualifying_member_events.sql
dbt/models/intermediate/int_redemption_validation.sql
dbt/models/marts/dim_date.sql
dbt/models/marts/dim_members.sql
dbt/models/marts/dim_offers.sql
dbt/models/marts/dim_partners.sql
dbt/models/marts/fct_redemptions.sql
dbt/models/marts/mart_cohort_retention.sql
dbt/models/marts/mart_executive_kpis.sql
dbt/models/marts/mart_member_engagement.sql
dbt/models/marts/mart_partner_performance.sql
dbt/models/staging/_seeds.yml
dbt/models/staging/stg_member_events.sql
dbt/models/staging/stg_members.sql
dbt/models/staging/stg_membership_status_history.sql
dbt/models/staging/stg_offer_eligibility.sql
dbt/models/staging/stg_offers.sql
dbt/models/staging/stg_partner_categories.sql
dbt/models/staging/stg_partners.sql
dbt/models/staging/stg_redemptions.sql
dbt/models/staging/stg_simulation_period.sql
dbt/profiles/profiles.yml
dbt/tests/assert_cohort_retention_bounds.sql
dbt/tests/assert_completed_redemptions_are_valid.sql
dbt/tests/assert_dim_date_is_contiguous.sql
dbt/tests/assert_kpi_population_bounds.sql
dbt/tests/assert_member_month_grain.sql
dbt/tests/assert_monthly_active_members_reconciliation.sql
dbt/tests/assert_monthly_redemption_reconciliation.sql
dbt/tests/assert_one_valid_eligibility_interval_per_pair.sql
dbt/tests/assert_opportunity_grain.sql
dbt/tests/assert_partner_month_grain.sql
dbt/tests/assert_partner_population_bounds.sql
dbt/tests/assert_snapshot_kpis_reconcile_to_source.sql
dbt/tests/assert_status_intervals_valid.sql
docs/architecture/dbt-lineage.md
docs/architecture/dbt-model-plan.md
docs/architecture/powerbi-authoring-spec.md
docs/architecture/powerbi-implementation.md
docs/business/business-case.md
docs/business/requirements.md
docs/business/stakeholder-personas.md
docs/data/synthetic-data-contract.md
docs/evidence/G1-checkpoint.md
docs/evidence/G2-checkpoint.md
docs/evidence/G3-checkpoint.md
docs/evidence/G5-publication-inventory.md
docs/evidence/powerbi-acceptance-matrix.md
docs/evidence/powerbi-kpi-reconciliation.sql
docs/governance/decision-log.md
docs/governance/kpi-definition-checklist.md
docs/governance/kpi-dictionary.md
docs/governance/metrics-ownership.md
docs/images/powerbi/01-executive-overview.png
docs/images/powerbi/02-member-engagement.png
docs/images/powerbi/03-partner-performance.png
pyproject.toml
scripts/export_powerbi_snapshots.py
src/membership_metrics/__init__.py
src/membership_metrics/generate.py
src/membership_metrics/validate.py
tests/test_generator.py
tests/test_validation.py
uv.lock
```

## Explicitly excluded from this proposal

- `dbt/profiles/.user.yml`, all real `.env` files, and all machine-specific configuration. The selected `.env.example` contains only a placeholder value.
- The other tool-specific environment examples and Compose files for Lightdash/Metabase/MinIO; these are outside this portfolio's approved scope.
- Local databases, generated source inputs under `data/generated/`, dbt targets/logs, Python caches, virtual environments, egg-info/build artifacts, and OS metadata.
- PBIX/PBIT binaries, the original PDF, and all other unreviewed binaries. The three PNGs in the list are faithful 240-DPI page renders of the supplied three-page PDF; no charts were reconstructed, and these are not Desktop screenshots.
- Internal operational and historical documents excluded for local paths or scope, including `docs/PROJECT_STATUS.md`, `docs/evidence/G4-checkpoint.md`, `docs/evidence/G5-checkpoint.md`, `docs/evidence/P0-checkpoint.md`, `docs/architecture/feasibility-study.md`, and Metabase/Trivy audit files. These remain in the working tree; they were not deleted or rewritten for publication.

## Asset, licensing, and release notes

- No code or data license is added in this preparation. Recommendation: MIT for original code; a separate CC0 1.0 dedication for the wholly synthetic generated data/snapshot files, if the owner confirms that distribution intent. Do not assume a code license automatically licenses data or third-party content.
- The original PBIX/PDF are not in the proposed initial commit. If the owner later approves binary distribution, consider the PBIX only as a versioned GitHub Release attachment after a separate contents/privacy/license review; do not put it in ordinary Git history. PDF previews are the proposed repository form; do not upload the source PDF unless separately approved.
- A source/theme or logo license cannot be established from the PDF-derived preview alone. No separate theme package or asset license record is in this inventory. Do not redistribute a third-party logo or theme as a standalone asset; verify rights/attribution for branded content before public release.
- GitHub Actions has not run on GitHub. The workflow contains only a CI-scoped test database credential, not a repository or service secret.
