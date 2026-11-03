# dbt Model Plan — P3

## Data boundaries

`membership_metrics.generate` produces eight source CSVs, a simulation-period control CSV and `provenance.json` in a deterministic run folder. dbt's seed command loads those files into a `raw` schema; the `simulation_period` row preserves the declared inclusive date range for calendar generation. The seed files are the local synthetic source snapshot, not business-transformed models. No CSV copy is checked into Git.

## Model grains and dependencies

| Model | Layer | Grain / key | Responsibility |
|---|---|---|---|
| `members`, `membership_status_history`, `partner_categories`, `partners`, `offers`, `offer_eligibility`, `redemptions`, `member_events`, `simulation_period` | Raw dbt seeds | As defined in `docs/data/synthetic-data-contract.md` | Immutable local source snapshot, loaded explicitly by `dbt seed`. |
| `stg_*` (nine models) | Staging | Inherits source grain/key | Explicit casts, normalized column names and UTC event dates; no metric aggregation. |
| `int_redemption_validation` | Intermediate | One row per source `redemption_id` | Classifies complete/cancelled/reversed source events and checks offer validity, dated member-offer eligibility and active membership via one-to-one/unique-key left joins; tests enforce key and interval integrity to prevent row multiplication. |
| `int_qualifying_member_events` | Intermediate | One row per source `event_id` | Applies event allowlist and verifies active membership on event date. |
| `int_eligible_member_offer_period` | Intermediate | One distinct `(month_start, member_id, offer_id)` opportunity | Intersects membership/eligibility, offer validity and each full or partial reporting month; pair grain prevents member-level denominator inflation. |
| `fct_redemptions` | Mart | One valid completed source `redemption_id` | Validated event fact; many-to-one dimensions only. |
| `dim_members` | Mart | One `member_id` | Synthetic registration/cohort attributes; one row per member. |
| `dim_partners` | Mart | One `partner_id` | Static category plus active interval; one row per partner. |
| `dim_offers` | Mart | One `offer_id` | Partner, validity interval, title. |
| `dim_date` | Mart | One `date_day` from control start to end inclusive | Calendar reporting dates and complete/partial-month labels. |
| `mart_member_engagement` | Mart | One `(member_id, month_start)` for each registered member/month | Snapshot eligibility, rolling-30-day active status and monthly qualifying activity. Members remain in the cohort grid after inactivity. |
| `mart_partner_performance` | Mart | One `(partner_id, month_start)` for each active partner/month | Active-at-month-end state, available-offer denominator flag, distinct valid redemption events and engaged-partner flag. |
| `mart_cohort_retention` | Mart | One `(cohort_month, age_month)` | Cohort size and monthly-active retained members; incomplete calendar months excluded and labelled in source model. |
| `mart_executive_kpis` | Mart | One `month_start` | Wide monthly panel; snapshot measures and flow measures are explicitly named. Ratios calculated from pair/partner populations before aggregation and are non-additive. |

## Semantic rules that SQL tests must preserve

- Status, partner, offer and eligibility intervals are start-inclusive/end-exclusive; all event timestamps are converted to UTC `date` before assignment.
- Only distinct, unique source event IDs count. A duplicate ID is a data-quality failure, not another event.
- Valid redemptions require status `complete`, an existing offer, event inside offer validity, an active membership interval and an offer-eligibility interval on that date.
- KPI-06 redemption rate counts distinct eligible member-offer pairs with at least one valid redemption over distinct pairs eligible during the period. Multiple redemptions do not inflate the numerator.
- KPI-08 denominator is distinct active partners with at least one active offer and eligible member opportunity for at least one day in the period. Each partner counts once even when it has multiple offers.
- KPI-02/03/07 are month-end snapshots; KPI-04/05 are period flows. Do not sum snapshots across months.
- A zero denominator produces NULL, not zero. Numerators are subsets of their denominators.
- Invalid rows remain inspectable in `int_redemption_validation`; a business test fails publication when a completed event is invalid.

## Test strategy

1. Seed schema and key tests: not-null, unique and relationships.
2. Intermediate source rule tests: interval integrity; clean complete-redemption classification; qualifying event membership-at-date.
3. Mart tests: key uniqueness, foreign keys, KPI numerator/denominator bounds, partner/member set cardinalities, month completeness and independent reconciliation to staging/source queries.
4. Negative tests: Python validator's controlled corrupt copies establish the source-level defects are detected; dbt custom SQL tests additionally fail if clean warehouse rules are violated. Do not mutate the checked-in synthetic output to run negatives.

## Current scope / explicit non-goals

No snapshots or changing dimension versioning beyond the synthetic status-history fact. No actual revenue, paid conversion, campaign attribution, real exposure/impressions, household users, causal inference, or vendor reconciliation. This is a local analytical model, not a deployed enterprise warehouse.
