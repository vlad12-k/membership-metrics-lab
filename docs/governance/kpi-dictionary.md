# Governed KPI Dictionary

**Project:** fictional MemberLoop synthetic portfolio case study.  
**Version:** proposed v1.0, 2026-10-28. Definitions are project-owned design decisions, not employer definitions or real stakeholder agreements. Changes require a decision-log entry and version increment.

## Shared contracts

- Source records and identifiers are synthetic. Planned sources are `members`, `membership_status_history`, `offers`, `offer_eligibility`, `partners`, `partner_categories`, `redemptions`, `member_events`, and `calendar`.
- “Eligible on date” means the member has a status interval `status = 'active'` whose half-open validity interval contains the date and the relevant offer-eligibility interval (for offer denominators) also contains the date.
- A “qualifying activity” is a distinct, nonduplicate member event whose type is on an explicit allowlist and that occurred while the member's membership was eligible. Redemption events count toward engagement only if the redemption itself passed offer and eligibility validation.
- Business dates use UTC; intervals are start-inclusive/end-exclusive. Month reporting uses calendar months. Current partial months are marked and excluded from comparisons that require complete periods.
- Duplicate source identifiers are quality failures/quarantined; never count repeated rows as separate business events. A repeated redemption under a different valid redemption ID is a legitimate separate event unless business status indicates otherwise.
- Missing keys, dates, status or event type fail validation or are quarantined. Missing measures are not imputed as zero. A metric with a zero denominator is `NULL`/not defined, not 0%.

## KPI contracts

### KPI-01 — Total registered members

- **Description:** Cumulative count of distinct synthetic members registered on or before the reporting as-of date; not a count of currently active/eligible members.
- **Calculation:** `COUNT(DISTINCT member_id)` for `registration_date <= as_of_date`.
- **Numerator / denominator:** Numerator = distinct registered member IDs. Denominator = not applicable (count metric).
- **Window / date attribution:** Cumulative through the snapshot `as_of_date`; registration date attributes entry into the population.
- **Reporting grain:** One point-in-time count per as-of date; the time series is a snapshot, not additive across dates.
- **Eligible population / exclusions:** All synthetic member rows registered by as-of date, including members later inactive; exclude invalid/missing registration dates and duplicate member keys via quality failure.
- **Nulls / duplicates:** Null member ID/date is rejected; distinct key and uniqueness tests prevent duplicate inflation.
- **Owner:** Head of Analytics (fictional metric steward).
- **Planned sources/model:** `members` → `dim_members` / `mart_executive_kpis`.
- **Limitations:** No real account deletion/merge semantics; synthetic registration is a single date.
- **Validation:** Compare to independent distinct count on source members filtered by date; assert nondecreasing between snapshots absent a defined deletion/restatement policy.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition.

### KPI-02 — Eligible members

- **Description:** Distinct members with active membership status on the specified as-of date.
- **Calculation:** `COUNT(DISTINCT member_id)` whose active status interval contains `as_of_date`.
- **Numerator / denominator:** Numerator = distinct eligible member IDs. Denominator = not applicable.
- **Window / date attribution:** Point-in-time snapshot at UTC `as_of_date`; status valid on that date is attributed.
- **Reporting grain:** One count per as-of date.
- **Eligible population / exclusions:** Registered members with an active status interval on the date; exclude future registrations, inactive/expired intervals and invalid/overlapping status history.
- **Nulls / duplicates:** Null IDs/dates/status fail; duplicate intervals are not double-counted and cause a quality test failure.
- **Owner:** Operations Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `members`, `membership_status_history` → `int_membership_status_as_of` → `mart_executive_kpis`.
- **Limitations:** A single `active` status is a simulation rule, not a product or commercial membership policy.
- **Validation:** Compare to distinct member IDs in the interval reference query; assert eligible count ≤ total registered members for the same date.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition.

### KPI-03 — Active members (30-day)

- **Description:** Distinct members eligible at the as-of date who performed at least one qualifying activity during the 30 calendar dates ending on and including that date.
- **Calculation:** Distinct eligible member IDs with a valid activity date in `[as_of_date - 29 days, as_of_date]` and membership eligible on the event date and as-of date.
- **Numerator / denominator:** Numerator = distinct active member IDs. Denominator = eligible members as of date (used for optional rate only; this KPI is a count).
- **Window / date attribution:** Rolling 30 calendar days inclusive of UTC as-of date; event timestamp converted to UTC activity date.
- **Reporting grain:** One count per as-of date.
- **Eligible population / exclusions:** Members eligible both on activity date and as-of date; exclude passive/unapproved event types, invalid, duplicate, future or out-of-window events.
- **Nulls / duplicates:** Null member/event ID/time/type rejected; deduplicate by event ID, with duplicate IDs treated as quality failures.
- **Owner:** Marketing Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `member_events`, `membership_status_history` → `int_qualifying_member_activity` / `mart_member_engagement`.
- **Limitations:** 30 calendar dates is not exactly 720 hours; the event allowlist and timezone are simplifying assumptions.
- **Validation:** Test lower/upper window boundary inclusion, eligibility at both dates, excluded event type and distinct-member count.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition; rolling inclusive 30-date window selected.

### KPI-04 — Monthly active members

- **Description:** Distinct members with at least one qualifying activity during a UTC calendar month while membership is eligible on the activity date.
- **Calculation:** `COUNT(DISTINCT member_id)` by `month_start` after validating event type, unique event ID and membership-at-event.
- **Numerator / denominator:** Numerator = distinct active member IDs. Denominator = not applicable.
- **Window / date attribution:** Half-open month `[month_start, next_month_start)`; activity event timestamp attributes the month.
- **Reporting grain:** One count per calendar month; partial month is labelled separately.
- **Eligible population / exclusions:** Members eligible on at least one qualifying event date; exclude unqualified, invalid, duplicate or out-of-month events.
- **Nulls / duplicates:** Null ID/time/type rejected; duplicated event ID fails source quality and cannot inflate count.
- **Owner:** Marketing Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `member_events`, `membership_status_history`, `dim_date` → `mart_member_engagement`.
- **Limitations:** This is event activity, not app sessions, offer exposure, unique daily visitors or a measure of satisfaction.
- **Validation:** Reconcile month count with independently grouped distinct qualifying events; test UTC month-end and eligibility transition boundaries.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition.

### KPI-05 — Offer redemption count

- **Description:** Number of valid, unique redemption events in a reporting period.
- **Calculation:** Count unique `redemption_id` where redemption time is within offer validity, member is eligible for the offer at redemption time, redemption status is accepted/complete, and source key passes uniqueness.
- **Numerator / denominator:** Numerator = valid unique redemption events. Denominator = not applicable.
- **Window / date attribution:** UTC `redeemed_at` timestamp; month/day attributed by UTC redemption date.
- **Reporting grain:** Redemption event; aggregated by selected reporting period, offer, partner and category after one-to-many paths are controlled.
- **Eligible population / exclusions:** Accepted/complete synthetic redemption; exclude invalid status, duplicate ID, missing FK, ineligible member, redemption outside offer/status interval, cancellation/reversal if represented.
- **Nulls / duplicates:** Missing ID, member, offer or timestamp is rejected; duplicate IDs fail quality and do not count twice. Null status is invalid.
- **Owner:** Partnerships Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `redemptions`, `offers`, `offer_eligibility`, `membership_status_history`, `partners` → `fct_redemptions`.
- **Limitations:** No settlement, refund, financial value or actual revenue is represented; no conversion of counts into value.
- **Validation:** Assert unique redemption ID in fact; reconcile accepted valid source IDs; test valid-window endpoints and eligibility interval.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition.

### KPI-06 — Offer redemption rate

- **Description:** Share of distinct member-offer pairs eligible at least one day during the reporting period that recorded at least one valid redemption during that period.
- **Calculation:** `redeemed_eligible_member_offer_pairs / eligible_member_offer_pairs`.
- **Numerator / denominator:** Numerator = distinct `(member_id, offer_id)` pairs with ≥1 valid redemption in period and eligibility at redemption; denominator = distinct pairs with a nonempty eligibility interval overlapping the report period and an offer valid at least one day in that period. Numerator is a subset of denominator.
- **Window / date attribution:** Same reporting period for both; period is half-open `[start, end)` in UTC business dates. Eligibility is intersected with offer validity and period.
- **Reporting grain:** Period (optionally partner/category); calculate pair counts at the pair grain before aggregation. Rate is non-additive.
- **Eligible population / exclusions:** Unique eligible pairs exposed to an active offer at least one day; exclude expired/inactive offer portions, invalid offers, invalid redemptions and noneligible members.
- **Nulls / duplicates:** Null pair keys/intervals are invalid; duplicate redemptions do not add pair counts; zero denominator returns NULL/“not defined”.
- **Owner:** Marketing Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `offer_eligibility`, `offers`, `redemptions`, membership status → `int_offer_eligibility_period`, `fct_redemptions`, `mart_executive_kpis`.
- **Limitations:** Eligibility is a proxy for exposure; impressions, promotion visibility, campaign targeting and offer attractiveness are not modeled. This rate is not a causal conversion or redemption success probability.
- **Validation:** Assert `0 ≤ numerator ≤ denominator`; recompute eligible pairs independently; exercise no eligible pair, pair with multiple redemptions, and partial-period offer cases.
- **Version history:** v1.0, 2026-10-28 — pair-based denominator chosen to avoid member-level cross-offer denominator ambiguity.

### KPI-07 — Active partner count

- **Description:** Distinct partners whose platform status is active on the as-of date, regardless of whether they recorded a redemption.
- **Calculation:** Count unique partners with active status interval containing the as-of date.
- **Numerator / denominator:** Numerator = active partner IDs. Denominator = not applicable.
- **Window / date attribution:** Point-in-time UTC `as_of_date`; partner effective dates determine state.
- **Reporting grain:** One count per as-of date; partner category is the partner's single static v1 category.
- **Eligible population / exclusions:** Partners registered/activated by date and not deactivated before date; exclude test-only/invalid partner rows.
- **Nulls / duplicates:** Null partner IDs/status intervals rejected; duplicate partner key fails uniqueness test.
- **Owner:** Partnerships Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `partners` → `dim_partners` / `mart_partner_performance`.
- **Limitations:** Active means platform status only; it does not imply an active valid offer, contract, sales or partner commercial relationship.
- **Validation:** Distinct partner count reconciles with source status-as-of query; count is bounded by total known partners.
- **Version history:** v1.0, 2026-10-28 — initial proposed definition; intentionally independent of offer availability.

### KPI-08 — Partner engagement rate

- **Description:** Share of partners with at least one valid redemption among active partners offering at least one valid member-eligible offer during the reporting period.
- **Calculation:** `engaged_eligible_partner_count / partner_offer_available_count`.
- **Numerator / denominator:** Numerator = distinct denominator partners with ≥1 valid redemption attributed to the period. Denominator = distinct active partners with ≥1 offer that is valid and available to at least one eligible member for ≥1 day in the period. Numerator is a subset of denominator.
- **Window / date attribution:** Same calendar reporting period; valid redemption date attributes engagement; offer validity/availability intervals intersect the period.
- **Reporting grain:** Period, optionally category. Partner counted once per category because v1 assigns one category per partner.
- **Eligible population / exclusions:** Active partners with a genuine eligible offer opportunity; exclude inactive partners, invalid/expired offers and partners without an eligible audience opportunity.
- **Nulls / duplicates:** Missing partner/offer/key invalid; duplicate redemption events do not add partner counts; zero denominator returns NULL.
- **Owner:** Partnerships Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `partners`, `offers`, `offer_eligibility`, `redemptions` → `int_partner_offer_availability`, `mart_partner_performance`.
- **Limitations:** It measures participation in this synthetic event definition, not partner satisfaction, exposure, value, contract quality or causal performance.
- **Validation:** Assert numerator ≤ denominator; test partners with multiple offers/redemptions count once; independently reconcile partner sets.
- **Version history:** v1.0, 2026-10-28 — denominator narrowed to partners with a valid eligible offer opportunity.

### KPI-09 — Repeat redemption rate

- **Description:** Share of unique members with at least one valid redemption during the period who have at least two distinct valid redemption events in that period.
- **Calculation:** `repeat_redeemers / members_with_redemption`.
- **Numerator / denominator:** Numerator = distinct members with ≥2 valid unique redemption IDs. Denominator = distinct members with ≥1 valid unique redemption ID. Numerator is a subset.
- **Window / date attribution:** Both counts use the same UTC reporting period; redeemed-at date attributes each event.
- **Reporting grain:** Period; optional partner/category slice uses consistent member/event attribution and is non-additive across slices.
- **Eligible population / exclusions:** Members with valid offer/member eligibility at redemption time; exclude invalid, duplicate, cancelled/reversed or out-of-validity records.
- **Nulls / duplicates:** Null keys/time fail quality; duplicate redemption IDs never satisfy repeat threshold; zero denominator returns NULL.
- **Owner:** Finance Analyst (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `fct_redemptions` → `mart_member_engagement` / `mart_executive_kpis`.
- **Limitations:** A repeat event does not measure customer loyalty, incremental value or financial contribution; repeated use of one offer is included if event IDs differ and are valid.
- **Validation:** Assert `0 ≤ repeat members ≤ redeemer members`; check one-event and two-event reference members; validate duplicate-ID behavior.
- **Version history:** v1.0, 2026-10-28 — repeat defined as ≥2 valid events by distinct redemption IDs in the same reporting period.

### KPI-10 — Cohort retention rate

- **Description:** Share of the original eligible signup cohort with at least one qualifying, membership-eligible activity in cohort-relative calendar month `k`.
- **Calculation:** `distinct cohort members active in age_month / fixed cohort member count`.
- **Numerator / denominator:** Numerator = distinct cohort members with qualifying activity during the relative month while eligible on event date. Denominator = all valid members in the cohort at registration; fixed across age months. Numerator cannot exceed denominator.
- **Window / date attribution:** Cohort is UTC registration calendar month; age 0 is that month, age 1 the next calendar month. Cohort-relative month uses complete calendar months.
- **Reporting grain:** `(cohort_month, age_month)`; retention is non-additive and the denominator does not shrink with attrition.
- **Eligible population / exclusions:** Cohort members with valid registration and eligibility at registration; current cohort age periods without full follow-up are censored/excluded from complete-period comparisons, not assigned zero.
- **Nulls / duplicates:** Missing member/registration date rejected; duplicate member key fails quality; duplicate event IDs excluded and flagged; zero-sized cohort returns NULL.
- **Owner:** Marketing Manager (fictional metric owner); Head of Analytics is steward.
- **Planned sources/model:** `members`, status history, `member_events`, `dim_date` → `mart_cohort_retention`.
- **Limitations:** Activity is a proxy for retention; the synthetic data has no churn survey, member perception, marketing exposure or causal design. Retention need not be monotonic because a member can return.
- **Validation:** Assert `0 ≤ active cohort members ≤ cohort size`; test month-0, month-1, censored last period, and distinct cohort assignment; reconcile selected cohorts to member-level rows.
- **Version history:** v1.0, 2026-10-28 — fixed original cohort denominator and month-age semantics selected.

## Ownership and change control

Fictional owners are analytical accountability assignments, not real employee assignments. The owner proposes a definition change; Head of Analytics (steward) reviews grain, population, numerator/denominator, date attribution and downstream impact. Record the old/new definition, rationale, effective date, tests and affected reports in [`decision-log.md`](decision-log.md) before changing a published KPI. Do not silently redefine a metric in a visual.
