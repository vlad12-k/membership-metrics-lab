# Product and Analytical Requirements

**Status:** Proposed requirements for the fictional MemberLoop case study. No actual stakeholder interviews were conducted.

## Business questions and acceptance criteria

| ID | Question | Required metrics | Proposed analytical output | Acceptance criteria |
|---|---|---|---|---|
| BQ-01 | How many members are active over time? | Total registered; eligible members; 30-day active members; monthly active members | Executive cards and monthly activity trend | State the as-of date/window; show distinct member counts; eligible population and activity rule are traceable; complete periods are distinguished from partial period. |
| BQ-02 | What proportion of eligible members redeem an offer? | Offer redemption count; offer redemption rate | Period trend plus member-offer denominator and category/offer slice | Numerator uses valid deduplicated redemptions; denominator is eligible member-offer pairs; numerator cannot exceed denominator; zero denominator renders as undefined/blank, not 0%. |
| BQ-03 | Which partner categories drive engagement? | Active partner count; partner engagement rate; valid redemptions | Category table/trend with rates and absolute counts | Single category attribution per partner; rates show numerator/denominator; no many-to-many join multiplies redemptions. |
| BQ-04 | How do new-member cohorts retain engagement? | Cohort retention rate; monthly active members | Cohort-month matrix for fully observed periods | Cohort is registration month; each member appears in one cohort; month-zero baseline is defined; only mature periods are compared. |
| BQ-05 | Where could better reporting improve operational decisions? | All governed metrics; freshness and quality checks (planned) | Simulated walkthrough and quality/coverage indicators | Separate observation from recommendation; expose missingness, limitations and failing quality gates; no causal or financial impact claim. |

## Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Generate synthetic data deterministically from a documented seed and bounded date range. |
| FR-02 | Represent member status and offer eligibility as effective-dated intervals with start-inclusive/end-exclusive semantics. |
| FR-03 | Keep event, redemption and eligibility grains distinct; join only after aggregation to a declared grain or through a unique key. |
| FR-04 | Exclude duplicate redemption identifiers and invalid, ineligible or out-of-offer-window redemption records from valid-redemption metrics; expose reasons in quality reporting. |
| FR-05 | Provide canonical definitions for the ten KPIs in the KPI dictionary; reports must reference these definitions, not reimplement them independently. |
| FR-06 | Test key constraints, value domains, temporal rules, eligibility, numerator/denominator bounds, duplicate handling and reconciliation. |
| FR-07 | Keep deliberately invalid fixtures outside clean synthetic inputs and demonstrate that validators detect each seeded defect. |
| FR-08 | Provide one Power BI report with three pages: Executive Overview, Member Engagement and Partner Performance. The owner accepts the supplied presentation as-is; distinguish PDF-export evidence from unverified Windows Desktop behavior. |
| FR-09 | Show time basis, reporting period, units, valid/undefined denominator state and material limitations with reported metrics. |
| FR-10 | Capture model descriptions and a path from source → transformation → mart → metric → BI output. |

## Non-functional requirements

- **Reproducibility:** fixed seed, pinned Python dependency graph, recorded generator parameters and stable outputs.
- **Correctness:** declare row grain and temporal semantics; validate outputs using independent reference calculations.
- **Privacy:** synthetic data only; pseudonymous IDs; no real personal data or scraped employer data.
- **Security:** no secrets in source control; local-only BI service; no internet exposure, remote publication or external accounts.
- **Reliability:** safe reruns, explicit failure behavior, quarantine/rejection visibility, reproducible rebuild and reconciliation.
- **Maintainability:** small modules, readable SQL, meaningful model/column names, focused tests and concise documentation.
- **Cost:** £0 default; local open-source/free tools only. Any future paid tool needs owner approval.
- **Performance:** measure actual generation/build/report performance before making scalability claims; keep dataset modest enough for the local host.
- **Accessibility:** readable labels, understandable units, non-color-only cues, sensible contrast, no deceptive axes.

## Data model assumptions and grains (planned)

| Entity/model | Declared grain | Key and semantic notes |
|---|---|---|
| members | One row per synthetic member | `member_id` primary key; registration date is cohort assignment date. |
| membership_status_history | One row per member status interval | `(member_id, effective_start_date)` unique if intervals are normalized; `effective_end_date` is exclusive and may be NULL for open-ended current state; no overlaps. |
| partners | One row per partner | `partner_id` primary key; one static partner category in v1. |
| partner_categories | One row per category | `category_id` primary key. |
| offers | One row per offer | `offer_id` primary key; partner FK; validity is start-inclusive/end-exclusive date interval. |
| offer_eligibility | One row per member-offer eligibility interval | `(member_id, offer_id, effective_start_date)` unique; intervals cannot overlap for the same pair. |
| redemptions | One row per source redemption event | `redemption_id` primary key; contains member, offer and timestamp; duplicate IDs are rejected/quarantined, not silently collapsed. |
| member_events | One row per source member event | `event_id` primary key; only event types on the governed qualifying-event allowlist count toward activity. |
| dim_date | One row per calendar date | Unique `date_day`; continuous date spine. |
| fct_redemptions | One row per valid deduplicated redemption event | Redemption event ID is unique; partner/category dimensions joined via offer/partner with many-to-one cardinality. |
| mart_member_engagement | One row per member per reporting month | `(member_id, month_start)` unique; counts/flags derived from distinct event IDs after membership-at-event validation. |
| mart_partner_performance | One row per partner per reporting month | `(partner_id, month_start)` unique; aggregate valid redemptions first to avoid fan-out. |
| mart_cohort_retention | One row per signup cohort month and cohort-relative month | `(cohort_month, age_month)` unique; numerator distinct active members, denominator fixed eligible cohort members; partial follow-up excluded from comparisons. |
| mart_executive_kpis | One row per reporting month/as-of snapshot as required by metric type | KPI date grain explicit; do not combine point-in-time counts with additive flow counts without labeling. |

## Date and filter conventions

- Store event timestamps in UTC; derive reporting dates using a documented UTC reporting calendar for v1. No localized daylight-saving interpretation is inferred.
- All business validity intervals use `valid_from <= date < valid_to`; an open-ended `valid_to` means no known end.
- Monthly periods are calendar months in UTC. Current partial month is labeled partial and excluded from complete-month comparisons.
- Retention month 0 is the calendar month of registration; age 1 is the following calendar month. Cohort denominator is fixed at qualifying synthetic members registered in the cohort; members are not removed from historical denominators when they later become inactive.
- Filter dimensions may slice eligible populations only where the definition supports it. Reported denominator and numerator must use consistent attribution and filter semantics.

## Quality and release acceptance

- Every fact/mart table must state its grain and key in dbt docs.
- Source/target counts and valid/rejected row counts must be observable at each material boundary.
- Baseline synthetic pipeline passes constraints; controlled invalid fixtures trigger the expected tests.
- For each KPI, at least one independently computed reference example reconciles to the mart/BI output.
- Test suite protects date boundary, null denominator, duplicate ID, eligibility interval, repeated redemption, and incomplete cohort cases.
- A BI release is not accepted until Lightdash runs locally, filters and totals are exercised, screenshots are genuine application captures, and counts reconcile.
