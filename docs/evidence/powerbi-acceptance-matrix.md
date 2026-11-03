# G4 Power BI Acceptance Matrix

**Current status (owner decision 2026-11-02): presentation accepted AS-IS.** The supplied PBIX/PDF hashes match the prior audit; the owner explicitly accepts the existing presentation limitations and requests no visual changes. This does not upgrade Desktop execution evidence: Refresh, Reopen, relationships, filter interactions, local paths and accessibility remain **NOT VERIFIED**. Missing evidence is never PASS.

| Requirement | Evidence / test | Status | Remaining action / owner |
|---|---|---|---|
| PBIX/PDF received and integrity checked | PBIX 444,132 bytes, SHA-256 `0a028f1961159c7a4cb0208bc148b909a3914b14419bd492fc56d0c68a6a02ea`; PDF 328,222 bytes, SHA-256 `2e03577c8ec67d8a194a595f96fd6a6304e7024c5d43c4bdea00a66ca755aff1`. Both match the previously audited versions. PBIX package structure/CRC passed previously; PDF has three pages. | PASS (artifact only; owner accepted AS-IS) | Preserve received files; no new export requested. |
| Report page structure | PBIX package lists Executive Overview, Member Engagement and Partner Performance; one report with three pages, not three distinct reports. | PASS (package structure only) | Desktop rendering remains NOT VERIFIED. |
| PDF presentation | Prior review identified a partial visible cohort-matrix viewport, ambiguous 101,038 opportunity wording and decimal formatting on integer counts. Identical PDF hash confirms the same accepted artifact. | OWNER-ACCEPTED AS-IS | Preserve as supplied; disclose these limitations. No visual changes requested. |
| Four previously validated dbt marts identified | Export script allowlist and manifest identify `mart_executive_kpis`, `mart_member_engagement`, `mart_partner_performance`, `mart_cohort_retention`; G3 build evidence: [`G3-checkpoint.md`](G3-checkpoint.md) | PASS | None for snapshot scope |
| Schema, grain, row counts, time semantics, source dependencies | Manifest records columns/types/nullability, grain, period range and UTC/date semantics; model SQL and [`dbt-lineage.md`](../architecture/dbt-lineage.md) define upstream dependencies | PASS | Keep manifest with snapshots |
| Read-only, synthetic exports | Manifest records synthetic classification, `lightdash_reader`, read-only repeatable-read transaction, UTC; exporter checks mart-only SELECT and read-only state | PASS | None |
| Deterministic CSV contents and integrity | SHA-256 stored in manifest; second export repeated and CSV hashes unchanged; independent checker verified file hash, header/schema and row count | PASS | Timestamp in manifest changes by design |
| Snapshot row counts and grain uniqueness | 18 executive, 95,148 member-month, 2,279 partner-month, 171 cohort-age; independent duplicate-key checks passed; total 97,616 | PASS | Recheck after any re-export or replacement |
| Synthetic data explicitly disclosed | Manifest classification and [`synthetic-data-contract.md`](../data/synthetic-data-contract.md) | PASS | Do not transfer to real data |
| Independent SQL reconciliation for governed KPIs | `powerbi-kpi-reconciliation.sql` produced 351/351 matches, 0 failures; KPI-01..09: 18 each; KPI-10: 171; XREF-05: 18; output CSV hash in manifest | PASS (SQL/mart only) | Reconcile report/DAX outputs again after actual Desktop build |
| Numerator/denominator consistency | All SQL checks matched; output contains actual/reference numerator and denominator; dictionary contracts define subset and denominator rules | PASS (SQL/mart only) | Verify card, month filters and category slices in Desktop |
| Timestamp/date-window semantics | UTC documented in manifest and KPI dictionary; month date ranges 2024-07 to 2025-12; complete/incomplete cohort semantics preserved | PASS (source) | Validate Desktop import and period filters |
| Power BI Desktop/Windows environment | No environment record or About dialog screenshot in the handoff | NOT VERIFIED | No evidence supplied; do not claim a Desktop environment was verified. |
| PBIP support/version | No Desktop/version evidence supplied | NOT VERIFIED | No PBIP claim is made. |
| Power BI model relationships/cardinality | No model-view screenshot or exported relationship evidence supplied. The authoring spec remains a proposal, not evidence of the actual model. | NOT VERIFIED | No relationship behavior is claimed as verified. |
| Three report pages | PBIX package definitions list the three expected page names; no Desktop rendering evidence supplied. | PASS (package structure); NOT VERIFIED (Desktop) | Report package page metadata only; no Desktop screenshot. |
| DAX outputs and totals reconcile | Visible PDF KPI values matched the approved baseline in the previous audit; no Desktop DAX/query output or filter-context results were supplied. | NOT VERIFIED (Desktop) | Reconcile single-month and multi-month results, category/cohort slices, totals, blanks and zero denominators to SQL. |
| Null, duplicate and blank/zero-denominator behavior | Source keys/reconciliation and G3 tests are verified; current snapshot has no incomplete/censored-period example. | PARTIAL (source only) | Verify report blanks/zeros and slicer effects. Do not modify approved CSVs to synthesize missing cases. |
| Accessibility and visual quality | No Windows Desktop evidence or accessibility review results supplied. | NOT VERIFIED | No accessibility result is claimed; owner accepted presentation as-is. |
| Successful open, local CSV refresh and reopen | No Desktop log, screenshot or test record supplied. | NOT VERIFIED | No supporting evidence in the received handoff. |
| Genuine Desktop screenshots / actual results | Incoming directory contains only PBIX and PDF; no screenshot or acceptance log. | NOT PROVIDED | README gallery is explicitly PDF-derived; it is not Desktop evidence. |
| Cohort Matrix complete evidence / empty-value setting | PDF contains only the visible portion of a scrollable table; no separate complete-matrix evidence. “Don’t format” remains owner-reported, not independently evidenced. | OWNER-ACCEPTED LIMITATION / NOT VERIFIED | Do not alter the report or request a new export. Describe the PDF viewport limitation; do not claim complete Matrix coverage or verified formatting behavior. |
| No unresolved critical data-quality defects | Prior G3 `dbt build` passed 151/151 nodes; exporter/schema/key checks passed; SQL reconciliation 351/351 | PASS (checked data scope) | Reassess if Desktop exposes import/type issues |
| Architecture, README, setup guide, KPI evidence and portfolio text | README now contains PDF-derived page previews and labels them as such; status wording distinguishes owner presentation acceptance from unverified Desktop tests. Historical evidence with local paths is excluded from the proposed public inventory. | PARTIAL | Preserve that distinction and validate the exact publication allowlist before commit. |
| Metabase remains blocked; evidence/images/volumes preserved | Prior scan/evidence retained; owner directed no more image experiments; no cleanup performed | PASS (decision) | No Metabase pulls/startup/risk acceptance under this plan |
| Lightdash-specific skills gap preserved | ADR, known gaps and job-requirement matrix state Power BI is not Lightdash experience | PASS (documentation) | Do not equate tool familiarity |
| No cloud publication/deployment/account/paid service | Local snapshot work only; no Power BI Service use | PASS (scope) | Separate owner approval required for any future external action |

## Page-level acceptance matrix

These December values are SQL/snapshot references. The visible PDF values matched them in the prior audit; this is **not** proof of Desktop behavior. Desktop page validation remains NOT VERIFIED until genuine Windows evidence is recorded.

| Page | Required evidence and acceptance checks | SQL reference for 2025-12 | Current status |
|---|---|---|---|
| Executive Overview | KPI cards, monthly member and redemption trends, reporting-month slicer; clarify active-member card as Last 30 Days. | 10,000 registered; 8,271 eligible; 1,456 active 30-day; 1,544 monthly active; **1,462 December events**; **1,326 / 19,667 = 6.7422586%**. | PDF values match; title fix not present; Desktop NOT VERIFIED |
| Member Engagement | Monthly activity, rolling 30-day, cohort × age matrix; provide full supplementary matrix. Current export has no incomplete/censored rows; do not edit snapshots to fabricate them. | 1,544 monthly active; 1,456 active 30-day; **204 / 1,229 = 16.5988609%**. Dec cohort age 0: **116 / 553 = 20.9764919%**. | Visible PDF values match; matrix completeness FAIL; Desktop NOT VERIFIED |
| Partner Performance | Partner/category/month results; clarify selected-period opportunity-months, whole-number formatting; no offer-level ranking. | **224 active partners**; **157 / 168 = 93.4523810%**; 1,462 December events; 19,667 December opportunity-months. | Visible PDF values match; label/format fixes not present; Desktop NOT VERIFIED |

The implementation-ready M, DAX, model, accessibility and Windows procedure are in [`powerbi-authoring-spec.md`](../architecture/powerbi-authoring-spec.md). Exact December values above distinguish event count (KPI-05) from pair-based redemption rate (KPI-06); do not calculate the rate using 1,462 as numerator.

## Remaining owner-assisted steps

1. No further Power BI presentation changes or exports are requested; preserve the accepted artifacts.
2. Keep Refresh, Reopen, relationships, local CSV paths, filter interactions and accessibility at NOT VERIFIED unless existing supporting Desktop evidence is supplied.
3. The PDF-derived gallery is a presentation preview only; retain its source/provenance label and the visible-scrollable-table caveat.
4. Treat owner acceptance of appearance separately from technical verification. Do not infer Desktop functionality or accessibility.
5. GitHub release preparation is a separate approval gate; no remote publication is authorized here.

**Current recommendation:** owner has accepted the presentation as-is. Desktop operational and accessibility checks remain NOT VERIFIED; no PASS claim is made for them.
