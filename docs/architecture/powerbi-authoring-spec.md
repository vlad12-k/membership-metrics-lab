# Power BI authoring specification — G4B

**Status:** Implementation-ready preparation only. Power BI Desktop has not been opened in this session. These M and DAX definitions are proposed from the inspected snapshot schema and governed SQL/KPI contracts; none has been pasted into, executed, or verified by Power BI Desktop. G4 remains **IN_PROGRESS**.

**Scope:** Four existing synthetic mart CSVs only. No dbt model or CSV is changed. No Power BI Service publication, deployment, account creation, or remote repository action is authorized.

## 1. Evidence inspected

Inputs inspected: `data/powerbi/snapshots/2026-10-28/manifest.json`, all four mart CSV headers and values, `dbt/models/marts/mart_{executive_kpis,member_engagement,partner_performance,cohort_retention}.sql`, `dbt/models/_models.yml`, `docs/governance/kpi-dictionary.md`, `docs/evidence/powerbi-kpi-reconciliation.sql`, `data/powerbi/snapshots/2026-10-28/kpi-reconciliation.csv`, and `docs/architecture/powerbi-implementation.md`.

Verified snapshot evidence:

- 97,616 total rows: 18 executive month rows, 95,148 member-month rows, 2,279 partner-month rows, 171 cohort-age rows.
- Reporting-month range: 2024-07-01 through 2025-12-01; the manifest records UTC business-date semantics.
- CSV headers exactly match the manifest. Current exported rows contain no blank CSV cells; this does not change the schema's declared nullable metadata or the rule that undefined rates remain null/blank.
- PostgreSQL booleans are encoded as `t`/`f` text in the CSVs (not `true`/`false`). IDs must remain text. CSV itself has no type metadata.
- Every current `is_complete_month` value in the executive, member and cohort snapshots is `t`; this export contains no incomplete/censored reporting-month example. The M/DAX preserve the flag/NULL semantics, but that edge behavior cannot be runtime-tested from this snapshot without a separately approved fixture or later snapshot.
- Manifest classification is synthetic; it records the extraction as read-only, repeatable-read and UTC.
- SQL reconciliation is **351/351 matches, zero failures** (KPI-01..09: 18 each; KPI-10: 171; XREF-05: 18). This validates the snapshot/mart values against the independent SQL reference, not any Power BI implementation.
- `mart_partner_performance` has no `offer_id`; its actual grain is partner/category/month. Do not create offer-level rankings.

## 2. Exact source tables and types

Preserve the four table names below. The listed columns are the exact inspected CSV order; Power Query header checks below fail on additions, removals, reordering, or spelling changes rather than silently adapting.

| Table | Rows / grain | Exact columns and Power Query types |
|---|---|---|
| `mart_executive_kpis` | 18; one row per reporting month | `month_start` date; `month_end_date` date; `is_complete_month` logical; `total_registered_members` Int64; `eligible_members` Int64; `active_members_30d` Int64; `monthly_active_members` Int64; `offer_redemption_count` Int64; `eligible_member_offer_pairs` Int64; `redeemed_member_offer_pairs` Int64; `offer_redemption_rate` number; `active_partners_as_of_month_end` Int64; `partner_offer_available_count` Int64; `engaged_eligible_partner_count` Int64; `partner_engagement_rate` number; `members_with_redemption` Int64; `repeat_redeemers` Int64; `repeat_redemption_rate` number. |
| `mart_member_engagement` | 95,148; one row per `member_id` × `month_start` | `member_id` text; `registration_date` date; `cohort_month` date; `month_start` date; `month_end_date` date; `is_complete_month` logical; `is_eligible_as_of_month_end` logical; `is_monthly_active` logical; `is_active_30d_as_of_month_end` logical; `qualifying_event_count` Int64; `qualifying_event_count_30d` Int64. |
| `mart_partner_performance` | 2,279; one row per `partner_id` × `month_start` | `partner_id` text; `category_id` text; `category_name` text; `month_start` date; `month_end_date` date; `is_active_as_of_month_end` logical; `eligible_member_offer_pairs` Int64; `has_available_offer` logical; `valid_redemption_count` Int64; `is_engaged_eligible_partner` logical. |
| `mart_cohort_retention` | 171; one row per `cohort_month` × `age_month` | `cohort_month` date; `age_month` Int64; `cohort_size` Int64; `retained_members` Int64; `is_complete_month` logical; `cohort_retention_rate` number (nullable by contract). |

Dates in the exports are UTC-derived **business dates**, not timestamps needing a Power BI timezone conversion. `month_start` identifies the calendar reporting month; `month_end_date` is its recorded reporting end. `cohort_month` is the registration calendar month. Do not coerce IDs to numeric, multiply rate values by 100, replace null rates with zero, or reinterpret a business date as a timestamp.

## 3. Additivity and filter semantics

| Measure / source columns | Classification | Safe presentation rule |
|---|---|---|
| `total_registered_members`, `eligible_members` | Semi-additive point-in-time distinct-member snapshots | Show the selected month's value; never sum across months. |
| `active_members_30d`, `active_partners_as_of_month_end` | Semi-additive month-end snapshots | Show one month at a time; do not sum over time. Distinct entities can overlap across other slices. |
| `monthly_active_members`; distinct member counts from `mart_member_engagement` | Non-additive distinct counts across months | One-month values are valid; summing months would count member-months, not unique people for the period. |
| `offer_redemption_count`, `valid_redemption_count` | Additive event flows | May sum across selected months and partner/category rows, after confirming the event-grain cross-check. State whether the visual is monthly or selected-period total. |
| `eligible_member_offer_pairs`, `redeemed_member_offer_pairs` | Additive at **member-offer-month opportunity** grain in the current SQL contract; not a unique-pair count over a multi-month interval | Use in the same reporting month for KPI-06. A multi-month sum means pair-month opportunities, not distinct pairs over the full interval. |
| `partner_offer_available_count`, `engaged_eligible_partner_count`; distinct partner counts from partner-month rows | Distinct partner counts, non-additive across months | Calculate within one reporting month; do not sum across a multi-month selection. Category totals are safe only for the current single-category-per-partner contract. |
| `offer_redemption_rate`, `partner_engagement_rate`, `repeat_redemption_rate` | Non-additive ratios | Recompute numerator / denominator at the governed reporting grain; never sum or take a simple average of monthly rates. For a multi-month card, show and label the latest selected month. |
| `cohort_size`, `retained_members`, `cohort_retention_rate` | Non-additive across `age_month` because the same cohort denominator recurs at every age | A cohort × age cell is the canonical result. A pooled rate, if later required, must be a weighted ratio at one explicitly defined age and only across complete periods. Never sum rates or cohort sizes over age. |
| `qualifying_event_count` | Additive monthly event count at the exported member-month grain | A sum represents event activity across those member-month rows. |
| `qualifying_event_count_30d` | Rolling-window observation count; repeated windows can include the same event | Do not present its sum across months as unique events. Prefer the governed distinct-member `active_members_30d` count. |

The SQL dictionary's dates, eligible populations, numerator/denominator rules and NULL-on-zero-denominator semantics remain canonical. The DAX below only selects/aggregates the exported governed marts; it does not redefine eligibility logic.

## 4. Power Query M — exact local import

### 4.1 Windows folder and shared readers

Transfer/copy only the existing snapshot folder to an owner-approved **local** Windows path, for example `C:\MML\Snapshots\2026-10-28\`. This example is not an observed shared-folder mapping. Use the approved host/guest shared folder if one exists, or an owner-approved local/offline transfer; do not upload the files. In Desktop, create a text parameter named `SnapshotFolder` whose value ends in `\`.

Create a blank query named `fnReadSnapshot` and paste:

```powerquery-m
let
    ReadSnapshot = (fileName as text, expectedHeaders as list) as table =>
        let
            Raw = Csv.Document(
                File.Contents(SnapshotFolder & fileName),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
            ),
            Promoted = Table.PromoteHeaders(Raw, [PromoteAllScalars = true]),
            ActualHeaderText = Text.Combine(Table.ColumnNames(Promoted), "|"),
            ExpectedHeaderText = Text.Combine(expectedHeaders, "|"),
            Checked =
                if ActualHeaderText = ExpectedHeaderText then
                    Promoted
                else
                    error Error.Record(
                        "SnapshotSchemaMismatch",
                        "CSV header/order does not match the approved snapshot schema.",
                        [FileName = fileName, Expected = expectedHeaders, Actual = Table.ColumnNames(Promoted)]
                    )
        in
            Checked
in
    ReadSnapshot
```

`Csv.Document` reads the UTF-8 CSV with CSV quoting, and the header guard makes the import fail closed on schema drift.[1] Use a second blank query named `fxPostgresBoolean`:

```powerquery-m
(value as any) as nullable logical =>
    if value = null then
        null
    else
        let
            Normalized = Text.Lower(Text.Trim(Text.From(value, "en-US")))
        in
            if List.Contains({"t", "true"}, Normalized) then
                true
            else if List.Contains({"f", "false"}, Normalized) then
                false
            else
                error Error.Record(
                    "UnexpectedBoolean",
                    "Expected PostgreSQL CSV boolean t/f (or true/false).",
                    [Value = value]
                )
```

The explicit `t`/`f` conversion is required by the inspected files. Keep null as null. Apply explicit type conversions with culture `en-US`; Power Query raises an error for a missing column when using the specified `MissingField.Error` behavior.[2]

### 4.2 Four CSV queries

Create one query per table. In each `expectedHeaders` list preserve the exact order from §2. For compactness, use these exact query bodies (the `TransformColumnTypes` lists below include every non-boolean column):

**`mart_executive_kpis`**

```powerquery-m
let
    Source = fnReadSnapshot("mart_executive_kpis.csv", {
        "month_start", "month_end_date", "is_complete_month", "total_registered_members",
        "eligible_members", "active_members_30d", "monthly_active_members", "offer_redemption_count",
        "eligible_member_offer_pairs", "redeemed_member_offer_pairs", "offer_redemption_rate",
        "active_partners_as_of_month_end", "partner_offer_available_count", "engaged_eligible_partner_count",
        "partner_engagement_rate", "members_with_redemption", "repeat_redeemers", "repeat_redemption_rate"
    }),
    Booleans = Table.TransformColumns(Source, {{"is_complete_month", fxPostgresBoolean, type nullable logical}}),
    Typed = Table.TransformColumnTypes(Booleans, {
        {"month_start", type date}, {"month_end_date", type date},
        {"total_registered_members", Int64.Type}, {"eligible_members", Int64.Type},
        {"active_members_30d", Int64.Type}, {"monthly_active_members", Int64.Type},
        {"offer_redemption_count", Int64.Type}, {"eligible_member_offer_pairs", Int64.Type},
        {"redeemed_member_offer_pairs", Int64.Type}, {"offer_redemption_rate", type number},
        {"active_partners_as_of_month_end", Int64.Type}, {"partner_offer_available_count", Int64.Type},
        {"engaged_eligible_partner_count", Int64.Type}, {"partner_engagement_rate", type number},
        {"members_with_redemption", Int64.Type}, {"repeat_redeemers", Int64.Type},
        {"repeat_redemption_rate", type number}
    }, [Culture = "en-US", MissingField = MissingField.Error])
in
    Typed
```

**`mart_member_engagement`**

```powerquery-m
let
    Source = fnReadSnapshot("mart_member_engagement.csv", {
        "member_id", "registration_date", "cohort_month", "month_start", "month_end_date",
        "is_complete_month", "is_eligible_as_of_month_end", "is_monthly_active",
        "is_active_30d_as_of_month_end", "qualifying_event_count", "qualifying_event_count_30d"
    }),
    Booleans = Table.TransformColumns(Source, {
        {"is_complete_month", fxPostgresBoolean, type nullable logical},
        {"is_eligible_as_of_month_end", fxPostgresBoolean, type nullable logical},
        {"is_monthly_active", fxPostgresBoolean, type nullable logical},
        {"is_active_30d_as_of_month_end", fxPostgresBoolean, type nullable logical}
    }),
    Typed = Table.TransformColumnTypes(Booleans, {
        {"member_id", type text}, {"registration_date", type date}, {"cohort_month", type date},
        {"month_start", type date}, {"month_end_date", type date},
        {"qualifying_event_count", Int64.Type}, {"qualifying_event_count_30d", Int64.Type}
    }, [Culture = "en-US", MissingField = MissingField.Error])
in
    Typed
```

**`mart_partner_performance`**

```powerquery-m
let
    Source = fnReadSnapshot("mart_partner_performance.csv", {
        "partner_id", "category_id", "category_name", "month_start", "month_end_date",
        "is_active_as_of_month_end", "eligible_member_offer_pairs", "has_available_offer",
        "valid_redemption_count", "is_engaged_eligible_partner"
    }),
    Booleans = Table.TransformColumns(Source, {
        {"is_active_as_of_month_end", fxPostgresBoolean, type nullable logical},
        {"has_available_offer", fxPostgresBoolean, type nullable logical},
        {"is_engaged_eligible_partner", fxPostgresBoolean, type nullable logical}
    }),
    Typed = Table.TransformColumnTypes(Booleans, {
        {"partner_id", type text}, {"category_id", type text}, {"category_name", type text},
        {"month_start", type date}, {"month_end_date", type date},
        {"eligible_member_offer_pairs", Int64.Type}, {"valid_redemption_count", Int64.Type}
    }, [Culture = "en-US", MissingField = MissingField.Error])
in
    Typed
```

**`mart_cohort_retention`**

```powerquery-m
let
    Source = fnReadSnapshot("mart_cohort_retention.csv", {
        "cohort_month", "age_month", "cohort_size", "retained_members",
        "is_complete_month", "cohort_retention_rate"
    }),
    Booleans = Table.TransformColumns(Source, {{"is_complete_month", fxPostgresBoolean, type nullable logical}}),
    Typed = Table.TransformColumnTypes(Booleans, {
        {"cohort_month", type date}, {"age_month", Int64.Type}, {"cohort_size", Int64.Type},
        {"retained_members", Int64.Type}, {"cohort_retention_rate", type number}
    }, [Culture = "en-US", MissingField = MissingField.Error]),
    AddReportingMonth = Table.AddColumn(
        Typed,
        "reporting_month",
        each Date.AddMonths(Date.StartOfMonth([cohort_month]), [age_month]),
        type date
    )
in
    AddReportingMonth
```

`reporting_month` is a Power BI filter key only: age 0 maps to the cohort's calendar month; age 1 maps to the next calendar month. `Date.AddMonths` performs this calendar-month shift.[3] Independent inspection confirmed the derived values cover 2024-07-01 through 2025-12-01 (18 reporting months) across 171 cohort-age rows. Do not replace `cohort_month` with this reporting key.

### 4.3 `DimReportingMonth`

Create this reference query after the executive CSV query is loaded. It contains one row per month and is a month dimension—not a daily date table.

```powerquery-m
let
    Source = Table.SelectColumns(mart_executive_kpis, {"month_start", "month_end_date", "is_complete_month"}),
    DistinctMonths = Table.Distinct(Source, {"month_start"}),
    UniqueCheck =
        if Table.RowCount(Source) = Table.RowCount(DistinctMonths) then
            DistinctMonths
        else
            error Error.Record("DuplicateMonth", "Executive mart must contain one row per month_start.", null),
    Sorted = Table.Sort(UniqueCheck, {{"month_start", Order.Ascending}}),
    AddMonthLabel = Table.AddColumn(Sorted, "MonthLabel", each Date.ToText([month_start], "yyyy-MM", "en-US"), type text)
in
    AddMonthLabel
```

Expected result: 18 rows, unique `month_start`, ordered 2024-07 through 2025-12. Keep both `month_start` and `MonthLabel`; use `MonthLabel` only for display and sort it by `month_start` in the model.

## 5. Semantic model and relationships

Use exactly five model tables: the four imported marts plus `DimReportingMonth`. No fact-to-fact relationships and no invented entity dimensions.

| From | To | Cardinality | Cross-filter | Active | Rationale |
|---|---|---|---|---|---|
| `DimReportingMonth[month_start]` | `mart_member_engagement[month_start]` | 1:* | Single, dimension → mart | Yes | Month appears once in the dimension and many times at member-month grain. |
| `DimReportingMonth[month_start]` | `mart_partner_performance[month_start]` | 1:* | Single, dimension → mart | Yes | Month appears once in the dimension and many times at partner-month grain. |
| `DimReportingMonth[month_start]` | `mart_cohort_retention[reporting_month]` | 1:* | Single, dimension → mart | Yes | A reporting month can have multiple cohort-age rows. `cohort_month` remains a separate analytical attribute, not a second active date relationship. |
| `DimReportingMonth` ↔ `mart_executive_kpis` | **No relationship** | — | — | — | Both sides have the same 18 unique months; Power BI's 1:1 relationship is necessarily bidirectional. Keep the model's filter flow one-way and transfer month filters explicitly in executive measures with `TREATAS`. |

The no-relationship choice is deliberate, not an omission. Power BI defines 1:1 relationships as filtering in both directions; the other three relationships can remain dimension-to-fact single direction.[4] `TREATAS` applies a reporting-month selection to the unrelated executive table within a measure.[5] This prevents an executive fact table from becoming a reverse filter route into the other marts. Do not add a direct fact-to-fact relationship to make the slicer work.

Hide technical identifiers and the derived `reporting_month` key from the report field list unless a detail table needs them. Keep `cohort_month`, `age_month`, `category_name`, and `MonthLabel` visible. Do not mark `DimReportingMonth` as a standard daily date table; it is a sparse 18-row month dimension. Validate actual relationship properties in Desktop before accepting the model.

## 6. DAX measures — proposed, not Desktop-tested

Add the measures below to a dedicated measures table if desired; that table must have no relationships. Names in code are exact. Format counts with `#,##0`; format rates as `0.00%` (the stored fraction is not multiplied by 100). The executive mart is intentionally disconnected, so executive measures use `TREATAS`.

### 6.1 DAX library

```DAX
Latest Selected Reporting Month =
MAX ( 'DimReportingMonth'[month_start] )
```

```DAX
Registered Members (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
RETURN
    CALCULATE (
        MAX ( 'mart_executive_kpis'[total_registered_members] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
```

```DAX
Eligible Members (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
RETURN
    CALCULATE (
        MAX ( 'mart_executive_kpis'[eligible_members] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
```

```DAX
Active Members 30D (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
RETURN
    CALCULATE (
        MAX ( 'mart_executive_kpis'[active_members_30d] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
```

```DAX
Monthly Active Members (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
RETURN
    CALCULATE (
        DISTINCTCOUNT ( 'mart_member_engagement'[member_id] ),
        KEEPFILTERS ( 'mart_member_engagement'[is_monthly_active] = TRUE () ),
        KEEPFILTERS ( 'DimReportingMonth'[month_start] = AsOfMonth )
    )
```

```DAX
Redemption Events (Selected Period) =
CALCULATE (
    SUM ( 'mart_executive_kpis'[offer_redemption_count] ),
    TREATAS (
        VALUES ( 'DimReportingMonth'[month_start] ),
        'mart_executive_kpis'[month_start]
    )
)
```

```DAX
Offer Redemption Rate (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
VAR RedeemedPairs =
    CALCULATE (
        MAX ( 'mart_executive_kpis'[redeemed_member_offer_pairs] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
VAR EligiblePairs =
    CALCULATE (
        MAX ( 'mart_executive_kpis'[eligible_member_offer_pairs] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
RETURN
    DIVIDE ( RedeemedPairs, EligiblePairs )
```

```DAX
Active Partners (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
RETURN
    CALCULATE (
        DISTINCTCOUNT ( 'mart_partner_performance'[partner_id] ),
        KEEPFILTERS ( 'mart_partner_performance'[is_active_as_of_month_end] = TRUE () ),
        KEEPFILTERS ( 'DimReportingMonth'[month_start] = AsOfMonth )
    )
```

```DAX
Partner Engagement Rate (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
VAR EngagedPartners =
    CALCULATE (
        DISTINCTCOUNT ( 'mart_partner_performance'[partner_id] ),
        KEEPFILTERS ( 'mart_partner_performance'[is_engaged_eligible_partner] = TRUE () ),
        KEEPFILTERS ( 'DimReportingMonth'[month_start] = AsOfMonth )
    )
VAR PartnersWithOffer =
    CALCULATE (
        DISTINCTCOUNT ( 'mart_partner_performance'[partner_id] ),
        KEEPFILTERS ( 'mart_partner_performance'[has_available_offer] = TRUE () ),
        KEEPFILTERS ( 'DimReportingMonth'[month_start] = AsOfMonth )
    )
RETURN
    DIVIDE ( EngagedPartners, PartnersWithOffer )
```

```DAX
Repeat Redemption Rate (Latest Month) =
VAR AsOfMonth = [Latest Selected Reporting Month]
VAR RepeatRedeemers =
    CALCULATE (
        MAX ( 'mart_executive_kpis'[repeat_redeemers] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
VAR Redeemers =
    CALCULATE (
        MAX ( 'mart_executive_kpis'[members_with_redemption] ),
        TREATAS ( { AsOfMonth }, 'mart_executive_kpis'[month_start] )
    )
RETURN
    DIVIDE ( RepeatRedeemers, Redeemers )
```

```DAX
Valid Redemption Events (Partner Rows) =
SUM ( 'mart_partner_performance'[valid_redemption_count] )
```

```DAX
Eligible Member-Offer Opportunities (Partner Rows) =
SUM ( 'mart_partner_performance'[eligible_member_offer_pairs] )
```

```DAX
Cohort Retention Rate (Cell) =
VAR OneCohortAge =
    HASONEVALUE ( 'mart_cohort_retention'[cohort_month] )
        && HASONEVALUE ( 'mart_cohort_retention'[age_month] )
VAR CompletePeriod =
    SELECTEDVALUE ( 'mart_cohort_retention'[is_complete_month], FALSE () )
RETURN
    IF (
        OneCohortAge && CompletePeriod,
        SELECTEDVALUE ( 'mart_cohort_retention'[cohort_retention_rate] ),
        BLANK ()
    )
```

### 6.2 Measure contract, expected values and validation

| Measure | Definition / fields | Filter context and aggregation behavior | Expected SQL reference | Desktop validation required |
|---|---|---|---|---|
| `Registered Members (Latest Month)` | KPI-01; `total_registered_members` | Latest selected month; `MAX` of its one monthly snapshot row; never sum time. | 2025-12: **10,000**. | All 18 months match KPI-01; latest selected-month card behavior; compare member-month reference counts. |
| `Eligible Members (Latest Month)` | KPI-02; `eligible_members` | Latest selected month; point-in-time count; never sum time. | 2025-12: **8,271**. | All 18 months match KPI-02 and remain ≤ registered members. |
| `Active Members 30D (Latest Month)` | KPI-03; `active_members_30d` | Latest selected month; inclusive 30 UTC calendar dates ending at month end; never sum time. | 2025-12: **1,456**. | All 18 months match KPI-03; confirm this is not monthly active. |
| `Monthly Active Members (Latest Month)` | KPI-04; distinct `member_id` where `is_monthly_active = true` | Latest reporting month; distinct count from member-month rows, non-additive over months. | 2025-12: **1,544**. | Match KPI-04 for all 18 months; verify cohort filter slices this measure while the executive table is not involved. |
| `Redemption Events (Selected Period)` | KPI-05; `offer_redemption_count` | Sum of valid event flow over selected month keys transferred by `TREATAS`; multi-month card is a period total. | 2025-12: **1,462 events**. | Match KPI-05 each month; selected-period sum equals the sum of selected monthly rows; match XREF-05 partner sum. |
| `Offer Redemption Rate (Latest Month)` | KPI-06; `redeemed_member_offer_pairs / eligible_member_offer_pairs` | Same latest reporting month for numerator and denominator; `DIVIDE` returns blank at zero denominator. Not event count / pairs; never sum/average rates. | 2025-12: **1,326 / 19,667 = 6.7422586%**. | Match KPI-06 numerator, denominator and rate for all 18 months; confirm period slicer picks latest selected month, not an average. |
| `Active Partners (Latest Month)` | KPI-07; distinct `partner_id` where `is_active_as_of_month_end = true` | Latest reporting month and any selected `category_id`/`category_name`; do not sum across months. | 2025-12: **224**. | Match KPI-07 month totals and partner-month reference; check category subtotal and overall distinct count. |
| `Partner Engagement Rate (Latest Month)` | KPI-08; distinct engaged eligible partners / distinct partners with eligible offer (`is_engaged_eligible_partner`, `has_available_offer`) | Same latest reporting month and same category filters on numerator and denominator. Non-additive. | 2025-12: **157 / 168 = 93.4523810%**. | Match KPI-08 numerator, denominator and rate for all months; verify numerator ≤ denominator and category slices. |
| `Repeat Redemption Rate (Latest Month)` | KPI-09; `repeat_redeemers / members_with_redemption` | Same latest reporting month; `DIVIDE`; global monthly measure from executive mart, not offer/category breakdown. | 2025-12: **204 / 1,229 = 16.5988609%**. | Match KPI-09 numerator, denominator and rate for all 18 months; zero redeemer case remains blank. |
| `Valid Redemption Events (Partner Rows)` | Partner-month valid event flow; `valid_redemption_count` | Additive over selected months, partners and the mart's single category assignment; not offer-level. | 2025-12 sum: **1,462**, equal to executive and valid redemption fact count. | Match XREF-05 for all 18 months and the monthly executive event count; category sums reconcile to monthly total. |
| `Eligible Member-Offer Opportunities (Partner Rows)` | Partner-month opportunities; `eligible_member_offer_pairs` | Additive as partner-month opportunities for selected periods; not people, not unique pairs over a multi-month interval. | 2025-12 sum: **19,667**. | Compare category/partner subtotals to the partner mart and monthly sum to the executive denominator. Do not use as a category conversion rate without a category-specific redeemed-pair numerator. |
| `Cohort Retention Rate (Cell)` | KPI-10; `cohort_retention_rate`, `is_complete_month`, `cohort_month`, `age_month` | One cohort × relative age cell only; `SELECTEDVALUE`; incomplete rows and totals/subtotals intentionally blank. | Cohort 2025-12, age 0: **116 / 553 = 20.9764919%**. | Match KPI-10 all 171 cohort-age rows; test age-0/age-1 and inspect matrix totals remain blank. The current snapshot has no incomplete rows; validate censored-row blank behavior only with a separately approved fixture or later snapshot, never by editing the export. |
| `Latest Selected Reporting Month` | Helper; `DimReportingMonth[month_start]` | Returns the latest visible month; used by all latest-month cards and chart points. | No month filter: **2025-12-01**. | No filter, one-month selection, multi-month selection and each trend-axis point. |

For validation, compare counts and numerator/denominator integers exactly; compare rates at an absolute tolerance of `1e-8` on the fractional value, while also requiring exact numerator and denominator matches. The 2025-12 reference distinction is intentional: **1,462 valid redemption events** is KPI-05; **1,326 redeemed eligible member-offer pairs / 19,667 eligible pairs = 6.7422586%** is KPI-06. Do not substitute event count for the numerator or compute rate as 1,462 / 19,667. December reference values are synthetic scenario outputs, not real business evidence or benchmarks.

## 7. Report page specifications

### A. Executive Overview

| Visual | Exact mapping | Behavior / notes |
|---|---|---|
| KPI cards | `[Registered Members (Latest Month)]`, `[Eligible Members (Latest Month)]`, `[Active Members 30D (Latest Month)]`, `[Redemption Events (Selected Period)]`, `[Offer Redemption Rate (Latest Month)]` | Titles include the reference period; redemption-event card says “selected-period total”, other cards say “latest selected month”. December values: 10,000; 8,271; 1,456; 1,462; 6.74%. |
| Member trend | X=`DimReportingMonth[MonthLabel]`; values=`Registered Members (Latest Month)`, `Eligible Members (Latest Month)`, `Active Members 30D (Latest Month)`, `Monthly Active Members (Latest Month)` | Line chart; count axis; no aggregation across months beyond each month point. Provide concise definitions in tooltip/subtitle. |
| Redemption trend | X=`DimReportingMonth[MonthLabel]`; column value=`Redemption Events (Selected Period)` | One bar per reporting month; tooltip states valid unique events. |
| Redemption rate trend | X=`DimReportingMonth[MonthLabel]`; value=`Offer Redemption Rate (Latest Month)` | Separate percent visual; do not combine event counts and rate on one unlabelled axis. |
| Reporting-period slicer | `DimReportingMonth[MonthLabel]`, sorted by `month_start` | Multi-select permitted; cards' latest-month/period-total rules remain as documented. Display `is_complete_month` where applicable. |

### B. Member Engagement

| Visual | Exact mapping | Behavior / notes |
|---|---|---|
| Monthly activity trend | X=`DimReportingMonth[MonthLabel]`; values=`Monthly Active Members (Latest Month)` and optionally `Active Members 30D (Latest Month)` | Separate semantics in legend/tooltips: activity during calendar month vs eligible at month-end and active in the inclusive 30-day window. |
| Cohort activity comparison | X=`mart_member_engagement[cohort_month]` (month formatted); value=`Monthly Active Members (Latest Month)`; reporting month slicer from `DimReportingMonth` | Distinct member count filtered to `is_monthly_active=true`; don't sum cohort/month rows as unique people over time. |
| Cohort retention matrix | Rows=`mart_cohort_retention[cohort_month]`; columns=`age_month`; values=`Cohort Retention Rate (Cell)`; report period slicer uses `DimReportingMonth[MonthLabel]` | Age 0 is cohort month. Use the derived `reporting_month` relationship for period filtering; preserve blank censored periods; no meaningful total of rates. |
| Repeat engagement card/trend | `[Repeat Redemption Rate (Latest Month)]`; month axis=`DimReportingMonth[MonthLabel]` | Global monthly rate only; source has no offer/category-specific member-repeat numerator and denominator. Explain that repeat means ≥2 valid redemption events by a member in the same month. |
| Reporting period slicer | `DimReportingMonth[MonthLabel]` | Period selection affects the month-level activity and cohort reporting-month row; cohort membership remains `cohort_month`, not the selected report month. |

### C. Partner Performance

| Visual | Exact mapping | Behavior / notes |
|---|---|---|
| KPI cards | `[Active Partners (Latest Month)]`, `[Partner Engagement Rate (Latest Month)]`, `[Valid Redemption Events (Partner Rows)]`, `[Eligible Member-Offer Opportunities (Partner Rows)]` | First two are latest-month counts/rates; latter two are selected-period additive partner-month totals. Label the opportunity count as member-offer opportunities, not people. |
| Monthly redemption trend | X=`DimReportingMonth[MonthLabel]`; legend=`mart_partner_performance[category_name]`; value=`[Valid Redemption Events (Partner Rows)]` | Stacked/clustered column or small multiples; category event totals must reconcile to XREF-05. |
| Category comparison | Axis=`category_name`; values=`[Active Partners (Latest Month)]`, `[Partner Engagement Rate (Latest Month)]`, and/or `[Valid Redemption Events (Partner Rows)]` | Distinguish the latest-month measures from period flow; engagement numerator and denominator remain under the same category filter. |
| Partner detail | Rows=`partner_id` (optional visible ID), `category_name`; values=`valid_redemption_count`, `eligible_member_offer_pairs`, `is_active_as_of_month_end` as a status/field | Partner-month detail only. Sort by a selected-period event total only if clearly named; no offer-level ranking. |
| Reporting-period slicer | `DimReportingMonth[MonthLabel]` | Latest-month snapshot/rate cards and selected-period event/opportunity totals follow the distinct rules above. |

### Accessibility for all pages

Use descriptive titles containing metric, unit and period; label axes and percentage units; provide meaningful alt text for non-decorative visuals; maintain keyboard-operable slicers and logical tab order; use readable typography and verified contrast; do not encode status or performance by color alone; use labels/position as a second cue; use color-vision-safe palettes; provide definitions and limitations in tooltips or a visible note. Review at normal/high zoom and with keyboard navigation in actual Desktop. This is a checklist, not a completed accessibility audit.

## 8. Owner-assisted Windows workflow

1. **Confirm actual environment.** On Windows, record edition/version/build and system architecture from *Settings → System → About*. For Windows on ARM, confirm the prerequisite update documented in `powerbi-implementation.md`. In Power BI Desktop use *Help → About* and record the exact installed version; compare it with Microsoft's current supported release information. Do not infer Windows/VM compatibility from this macOS session.
2. **Confirm PBIP support.** Check the actual Desktop version and project options documented in `powerbi-implementation.md`. Try *File → Save as → Power BI Project (`.pbip`)* only if Desktop offers it; otherwise save a Desktop-created local PBIX. PBIP/PBIX existence and successful opening are acceptance evidence, not assumed outcomes.
3. **Copy and hash-check inputs.** Use the approved local Windows path only. Verify each CSV against `manifest.json` SHA-256 before import; for example, run `Get-ChildItem 'C:\MML\Snapshots\2026-10-28\mart_*.csv' | Get-FileHash -Algorithm SHA256` and compare every result with the manifest. Keep the manifest and reconciliation output beside the four snapshots. Do not edit/resave CSVs in Excel.
4. **Import and transform.** In Desktop choose *Get data → Blank query* to create `SnapshotFolder`, `fnReadSnapshot`, `fxPostgresBoolean`, the four exact table queries, `DimReportingMonth`, and the cohort `reporting_month` column from §4. Load all tables. Confirm rows: 18 / 95,148 / 2,279 / 171. Confirm IDs are text, dates are Date, counts are Whole number, rates are Decimal number, and PostgreSQL `t`/`f` became true/false. Any header, type, row-count, or key mismatch is a stop-and-investigate result.
5. **Build the model.** Create only the §5 relationships. Do not connect `mart_executive_kpis`; use the provided `TREATAS` DAX. Verify one-to-many, active, single-direction on the other three relationships. Check there are no direct fact-to-fact edges or ambiguous paths.
6. **Implement DAX.** Create the measures from §6 as written. Add descriptions and formats. Validate one month, multi-month, every trend point, category, cohort-age cell, matrix totals, blank/zero-denominator and period-edge behavior against the acceptance matrix. A formula copied into Desktop is not verified until its outputs are compared with SQL.
7. **Create the three pages.** Follow the field-to-visual mappings in §7. Check slicers, category interactions, cohort age, sorting, tooltips, tab order, contrast, labels, alt text and mobile/zoom presentation as applicable.
8. **Reconcile and record.** Compare Desktop values with `kpi-reconciliation.csv` and the expected references in §6. Record actual DAX result, SQL result, tolerance, month/category/cohort context and pass/fail in `docs/evidence/powerbi-acceptance-matrix.md`. Save only genuine application screenshots after pages are open and functioning.
9. **Save, close, reopen, refresh.** Save a Desktop-authored PBIP when supported (or PBIX); close Desktop; reopen that exact artifact; refresh from the same local snapshot folder; verify no errors and all three pages still work; capture the version, refresh time and real screenshots. Do not publish to Power BI Service.
10. **Keep G4 IN_PROGRESS** until import, model, DAX reconciliation, all three pages, refresh/reopen, genuine screenshots, accessibility review and limitations are evidenced in the acceptance matrix.

## 9. Acceptance matrix additions

These expected results are source-side references; the Power BI status remains **NOT STARTED** until the owner performs and records each test in Desktop.

| Page | Acceptance tests and expected reference | Status until Desktop evidence |
|---|---|---|
| Executive Overview | For 2025-12: 10,000 registered; 8,271 eligible; 1,456 30-day active; 1,544 monthly active; **1,462 redemption events**; **1,326 / 19,667 = 6.7422586% redemption rate**. Verify 18 monthly points, single/multi-month slicer behavior, latest-month snapshot/rate cards, selected-period event total, event/rate separation, complete-month flag and metric definitions. | NOT STARTED |
| Member Engagement | For 2025-12: 1,544 monthly active; 1,456 30-day active; **204 / 1,229 = 16.5988609% repeat redemption rate**. Cohort `2025-12-01`, age 0: 553 cohort size, 116 retained, 20.9764919%. Verify all 18 monthly counts, all 171 cohort-age cells, 18-month date mapping, distinct-count slicing and blank totals. Current snapshot has no incomplete/censored rows; require an approved fixture or later snapshot to test that branch, without altering the export. | NOT STARTED |
| Partner Performance | For 2025-12: **224 active partners**; **157 / 168 = 93.4523810% partner engagement**; **1,462 valid redemption events**; **19,667 eligible member-offer opportunities**. Verify 18 monthly category/partner totals, XREF-05 event reconciliation, single-category partner totals, active/engaged/offer slicers, and no offer-level ranking. | NOT STARTED |

## 10. Known limitations and boundary

- The snapshots are synthetic, aggregate/mart-level data and do not include all source-event columns.
- No offer ID exists in `mart_partner_performance`; offer-level report rows/rankings and category-level redemption rate from distinct redeemed pairs cannot be supported by these exports.
- KPI-06 is based on distinct redeemed eligible member-offer pairs divided by eligible pairs. Event count is a different measure. Eligibility is a proxy for offer exposure, not observed impressions or causal conversion.
- KPI-09 is the project-defined same-month ≥2-valid-event member share, not loyalty or financial value.
- KPI-10 is an activity-based retention proxy. The fixed cohort denominator repeats by age and must not be summed over age.
- Desktop import, relationships, M execution, DAX execution/reconciliation, report rendering, refresh, reopen, PBIP/PBIX creation and screenshots are unverified owner-side tasks.
- Do not change the CSVs/dbt models, restart Metabase/Lightdash, accept any CVE risk, publish to Power BI Service, deploy, commit, push, or create a remote repository under this preparation task.

## Sources

[1] https://learn.microsoft.com/en-us/powerquery-m/csv-document
[2] https://learn.microsoft.com/en-us/powerquery-m/table-transformcolumntypes
[3] https://learn.microsoft.com/en-us/powerquery-m/date-addmonths
[4] https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand
[5] https://learn.microsoft.com/en-us/dax/treatas-function-dax
