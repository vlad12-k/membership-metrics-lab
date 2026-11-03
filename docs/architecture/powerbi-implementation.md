# Power BI implementation and owner-assisted setup

**Status (2026-11-02):** Source reconciliation and artifact-level inspection are verified. The owner accepts the supplied PBIX (one report with three pages) and three-page PDF **as-is**; both match the prior audit hashes. The visible presentation limitations are documented, not remediation requests. Windows Desktop Refresh, Reopen, relationship/filter behavior and accessibility remain **NOT VERIFIED**; no runtime or screenshot claim is made.

## Purpose and architecture

The approved local path consumes only the four validated PostgreSQL/dbt marts exported under `data/powerbi/snapshots/2026-10-28/`. The architecture is:

```text
Synthetic source generator → PostgreSQL raw/staging/intermediate → validated dbt marts
                                                       ↓ read-only export (UTC, repeatable-read)
                                      typed CSV snapshots + manifest + SQL reconciliation
                                                       ↓ owner-side local import only
                                      Power BI Desktop / PBIP (if supported by installed version)
```

Power BI Desktop is a local authoring/verification destination, not a new data source of record. Keep SQL/dbt definitions canonical. No Power BI Service upload or cloud publication is within this decision.

## Environment prerequisites and observed status

- This session ran on macOS. No Power BI Desktop executable/application was found in the inspected local environment, and no Windows session was available to inspect. Owner Windows installation, VM/host support, tenant/account/license and Desktop version are **unknown**, not inferred.
- Microsoft lists Windows 10 or later as a Desktop minimum and states Windows on ARM requires the 2025-09 cumulative update **KB5065789**. Only the latest Desktop release is supported; at verification time Microsoft's release archive listed the August 2026 update. The owner must record the actual installed version and Windows build before implementation.[60][76]
- PBIP/PBIR project files are documented for source control and semantic/report definitions. Microsoft's external-editing workflow requires the August 2026 Desktop release or later and enables a preview option; external-change detection/reload remains preview even though PBIP/PBIR is generally available. Do not create project files outside Desktop or assume preview behavior is enabled.[78][79]
- Expected local-only workflow: transfer/use the snapshot files in the already approved project workspace on the owner's supported Windows machine. Do not upload to Power BI Service, create an account, publish/share, provision paid capacity, modify unrelated repositories, or move the snapshots to an unapproved location.

### Owner's environment confirmation checklist

Record these in the acceptance matrix (no credentials needed):

1. Windows edition, version/build, CPU architecture, and whether the machine is physical ARM64 or virtualized.
2. On Windows on ARM, confirm KB5065789 is installed. Record any virtualization product and its supported guest configuration; do not claim VM support from the Mac-side inventory.
3. Power BI Desktop install source and exact version from **Help → About** (or the installed-app metadata). Confirm it is the supported latest release.
4. If using PBIP, confirm **File → Options and settings → Options → Preview features** shows the relevant PBIP features; external-file reload is optional and should be described as preview.
5. Confirm the user can open local CSVs. No Power BI Service tenant/license is required for this local Desktop path.

## Validated inputs

All four exports were taken in a single UTC repeatable-read, read-only transaction using `lightdash_reader`, which has SELECT access to `marts` only. The manifest records PostgreSQL data types and nullability because CSV itself has no schema. Reporting period spans 2024-07-01 through 2025-12-01 (18 months).

| Source table | Rows | Grain | Key/time semantics | CSV SHA-256 |
|---|---:|---|---|---|
| `mart_executive_kpis` | 18 | One row per reporting month | `month_start` is UTC calendar-month start; snapshots/rates are non-additive over months | `b9ebf74026aed538f66fd424eb5c5df311fe145716108c892040be462306a236` |
| `mart_member_engagement` | 95,148 | One row per `member_id`, `month_start` | Text member ID; UTC business dates; member/month flags | `25f390bedc65dfe70b1abc053ada19cf04bf4e1db5ee1b3b2054623550e325aa` |
| `mart_partner_performance` | 2,279 | One row per `partner_id`, `month_start` | Text partner/category IDs; category label; partner-month activity | `4f2ed4e858ec9e6306ca141a08190b4038864a07adff9c5f50b9c558407bd98a` |
| `mart_cohort_retention` | 171 | One row per `cohort_month`, `age_month` | UTC registration cohort month; age is relative calendar month; incomplete rates are NULL | `6c58224dbbbd2b53e24118997c71bc267859c985fc778bba19c1801f5138905e` |

Manifest: [`../../data/powerbi/snapshots/2026-10-28/manifest.json`](../../data/powerbi/snapshots/2026-10-28/manifest.json). Total exported rows: 97,616. The CSV hashes and manifest were rechecked after a repeated export; CSV hashes were unchanged. The extraction timestamp in the manifest intentionally changes between exports.

### Import types

Use the recorded PostgreSQL schema in the manifest. At minimum:

- IDs (`member_id`, `partner_id`, `category_id`) → **Text**, never numeric.
- `*_date`, `month_start`, `cohort_month` → **Date** (not Date/Time; the sources already represent UTC business dates).
- The CSV booleans are PostgreSQL `t`/`f` strings; explicitly convert `t` → true and `f` → false in Power Query. Preserve null as null and fail on any unexpected token.
- `age_month` and integer counts → **Whole number**.
- Rate fields (`*_rate`) → **Decimal number**; format as percentage in visuals without multiplying the source value by 100.
- Preserve database NULL values as Power Query null / model BLANK. Do not replace an undefined rate with 0.

## Semantic model plan

1. Import each CSV as a separate table. Keep the source mart names or use clear human-readable names with a documented mapping.
2. Create `DimReportingMonth` with one unique `month_start` row for each of the 18 months; include `month_end_date`, `is_complete_month`, and a `yyyy-MM` label. This 18-row month dimension is sparse, not a continuous daily calendar; do not mark it as a standard date table.
3. Relationships: `DimReportingMonth[month_start]` → `mart_member_engagement[month_start]`, `mart_partner_performance[month_start]`, and derived `mart_cohort_retention[reporting_month]` are one-to-many, active, single-direction from month dimension to mart. Derive cohort `reporting_month` with `Date.AddMonths([cohort_month], [age_month])`; keep `cohort_month` and `age_month` as separate cohort axes. **Do not relate `DimReportingMonth` to `mart_executive_kpis`: both have exactly 18 unique month keys, so Power BI makes that a bidirectional 1:1.** Use the documented `TREATAS` measures in [`powerbi-authoring-spec.md`](powerbi-authoring-spec.md) to apply month context to the disconnected executive mart.
4. Do not relate the marts directly. The approved exports do not contain complete shared entity dimensions for building extra relationship paths.
5. Hide technical IDs from the report field list unless a visible detail table needs them. Give measures readable names and descriptions. Avoid unnecessary bidirectional filters and many-to-many relationships.

The exact schema guards, Power Query M, DAX measure definitions, relationship/filter rationale, report visual mappings and per-page acceptance values are in [`powerbi-authoring-spec.md`](powerbi-authoring-spec.md). Treat those formulas as untested templates until they are exercised in Desktop.

## Metric and DAX contract

The canonical definitions are [`../governance/kpi-dictionary.md`](../governance/kpi-dictionary.md); SQL model lineage is in `dbt/models/marts/`. Keep DAX to selection, controlled aggregation and presentation. Where a KPI is already present as a monthly mart value, use that value rather than reconstructing it from lower-grain data without an approved reason.

- **Snapshot counts** (registered, eligible, 30-day active, monthly active, active partners) and **monthly rates** (redemption, partner engagement, repeat redemption) are non-additive across months. On a multi-month selection, KPI cards should show the latest selected month and label that behavior; a month-axis chart shows each month's value. Never sum snapshot counts or average monthly rates across months.
- **Redemption event count** is a flow and may be summed across selected months. State whether a card is a single-month count or period total.
- **Rates** should be numerator/denominator ratios at their governed grain with `DIVIDE`/blank-safe behavior, or the already calculated monthly rate from the mart. The denominator must be consistent with the numerator and filter period. For example, KPI-06 uses eligible and redeemed distinct member-offer pairs; KPI-08 counts each partner once in the period; KPI-09 counts members with >=2 valid events over members with >=1; KPI-10 divides retained cohort members by the fixed cohort size at the same age.
- **Cohort retention** must never be summed over age. Use the supplied `cohort_retention_rate` for a cohort-age cell; for any all-cohort summary at a single age, calculate weighted `SUM(retained_members) / SUM(cohort_size)` and exclude incomplete periods. A matrix by cohort month × age month avoids misleading aggregation.
- The partner mart does not have an `offer_id`, so the approved source supports partner/category/month-level offer-opportunity and redemption performance only. Do not label it offer-level performance.

If DAX measures are needed, first write them in Desktop, capture their definitions in TMDL/PBIP if supported, then compare their output for every selected period and dimensional slice with `powerbi-kpi-reconciliation.sql` or a new, reviewed SQL reference query. The DAX formulas themselves are not verification evidence.

## Page specifications

### 1. Executive Overview

- Cards: Registered members (KPI-01), eligible members (KPI-02), 30-day active members (KPI-03), redemption events (KPI-05), and monthly redemption rate (KPI-06).
- Monthly trends from `mart_executive_kpis`; clearly distinguish the snapshot count and event flow. Add a reporting month slicer and complete-month indicator. A rate card over multiple selected months shows the last selected month, not a mean.

### 2. Member Engagement

- Monthly active members (KPI-04), 30-day activity context, member engagement by `cohort_month`, repeat redemption rate (KPI-09), and cohort retention (KPI-10) by cohort × age.
- Use period filters on reporting month. For retention, hide or visibly mark incomplete months; preserve NULL and show tooltip/annotation describing censoring.
- Explain that activity is a qualifying synthetic event proxy, not app sessions, satisfaction, churn, or causal retention.

### 3. Partner Performance

- Active partners (KPI-07), partner engagement rate (KPI-08), valid redemption event counts, and eligible member-offer pair counts by category/partner/month.
- Provide month comparison only with clearly defined period semantics. The model does not support offer-ID-level rankings; label category/partner output honestly.

### Accessible design and review

Use a restrained, consistent palette, sufficient contrast, readable text and titles that state metric/time context. Do not encode status or performance by color alone; use labels, shape or position as additional cues. Add descriptive titles/tooltips, logical tab order, keyboard-operable slicers and alt text for meaningful visuals. Review the report at normal and high zoom, with keyboard navigation, and use color-vision-safe palettes. These are review criteria only; no accessibility audit has been run on a Power BI report because none exists.

## Local owner-assisted workflow

1. Confirm the Windows/Power BI environment checklist above and record evidence in [`../evidence/powerbi-acceptance-matrix.md`](../evidence/powerbi-acceptance-matrix.md).
2. Use only `data/powerbi/snapshots/2026-10-28/` in the approved project workspace. Confirm each CSV hash against `manifest.json` before import. Keep all artifacts local.
3. In Power BI Desktop, select **Get data → Text/CSV** and load the four mart CSVs. Apply the explicit import types above; verify each table's row count and keys against the manifest.
4. Create the reporting-month dimension and relationships as specified. Verify cardinality shows one-to-many and cross-filter direction is single. Capture the model view only if useful as real application evidence.
5. Implement pages and measures from the governed KPI contracts. Use one-month and multi-month selections, a partial period, category slices, cohort × age cells, blanks/zero denominator and totals/subtotals as verification cases.
6. Compare every displayed KPI with the SQL reconciliation CSV/report and record exact DAX result, SQL reference and equality/tolerance in the acceptance matrix. Do not adjust the dbt models to make visuals match.
7. Save as PBIP only if the actual installed Desktop supports it; otherwise save a local PBIX. If both are saved, PBIX is a convenience artifact and PBIP is the source-controlled definition. Do not hand-author a report file.
8. Close and reopen the actual artifact, refresh from the local CSV folder, confirm all three pages and interactions, capture genuine screenshots from Desktop, and record version/date and screenshot paths.
9. Leave G4 IN_PROGRESS until every required page is created, reopened, refreshed and verified. No Service upload, sharing or publication is authorized.

## Verified SQL reference results

The independent SQL reconciliation output is [`../evidence/powerbi-kpi-reconciliation.sql`](../evidence/powerbi-kpi-reconciliation.sql) plus [`../../data/powerbi/snapshots/2026-10-28/kpi-reconciliation.csv`](../../data/powerbi/snapshots/2026-10-28/kpi-reconciliation.csv). It contains 351 checks: KPI-01 through KPI-09 each match 18 monthly rows, KPI-10 matches 171 cohort-age rows, and XREF-05 matches 18 cross-check rows. **351/351 matched; zero failures.** This verifies the exported mart values and independent SQL calculations, not Power BI visuals/DAX.

For synthetic 2025-12, direct SQL reconciliation reports 10,000 registered, 8,271 eligible, 1,456 active over the inclusive 30-day window, 1,544 monthly active, 1,462 valid redemption events, and a 6.7423% offer redemption rate (1,326 redeemed distinct member-offer pairs / 19,667 eligible pairs). It reports 224 active partners, a 93.4524% partner engagement rate (157 / 168 eligible active partners), and a 16.5989% repeat redemption rate (204 / 1,229 members with redemption). These are generated scenario outputs, not real business evidence or benchmarks.

## Evidence and status

- Snapshot CSVs and manifest: `data/powerbi/snapshots/2026-10-28/`
- Exporter: `scripts/export_powerbi_snapshots.py`
- Independent SQL: `docs/evidence/powerbi-kpi-reconciliation.sql`
- Reconciliation result: `data/powerbi/snapshots/2026-10-28/kpi-reconciliation.csv`
- Acceptance: `docs/evidence/powerbi-acceptance-matrix.md`
- Decision: `docs/adr/0003-power-bi-desktop-g4.md`
- A PBIX report and PDF are received, but no Desktop model/relationship properties, Windows version, application refresh/reopen, interactions, screenshots, license/account or Service publication are verified. Owner-side Windows evidence and the presentation corrections in the acceptance matrix remain the execution dependencies.

## Sources

[60] https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop — Download Power BI Desktop - Power BI
[76] https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-latest-update-archive — Previous monthly updates to Power BI Desktop and the Power BI service
[78] https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview — Power BI Desktop projects
[79] https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-external-editing — Edit Power BI Desktop project files outside Power BI Desktop
