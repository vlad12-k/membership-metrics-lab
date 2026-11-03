# Business Case — Fictional Membership Discount Platform

**Status:** Proposed synthetic case study; no real business or stakeholder research was conducted.  
**Platform name:** MemberLoop (fictional). This name and all scenarios are invented for analytics simulation and have no connection to Blue Light Card or another real membership business.

## Context and problem

MemberLoop hypothetically connects members to discounts offered by partner businesses. Product, marketing, partnerships, finance and operations teams need shared answers about membership eligibility, offer engagement and partner activity. Inconsistent definitions of “active”, ambiguous eligible populations, duplicate redemption records and time-window mismatches can make competing reports disagree.

This project will demonstrate a governed analytics approach: write decision questions, define KPI contracts and ownership, model data at explicit grains, test business rules, and expose reusable reporting through a local BI layer. It is not based on interviews, operational data, or measured business outcomes.

## Business objective

Enable the fictional teams to make more consistent decisions about member engagement and partner offer performance by using traceable, reproducible metrics. The project will demonstrate how report quality depends on agreed definitions and validated data, not claim that it improved a real organisation's outcomes.

## Questions and proposed analytical outputs

| Business question | Governed KPIs | Proposed output | Decision it could inform (hypothetical) |
|---|---|---|---|
| How many members are active over time? | Eligible members; 30-day active members; monthly active members; total registered members | Executive overview with point-in-time eligible/active cards and monthly trend | Whether engagement changes merit investigation; not a causal explanation |
| What proportion of eligible members redeem an offer? | Offer redemption rate; offer redemption count | Offer redemption trend and category breakdown using eligible member-offer pairs as denominator | Where eligible audience conversion merits further analysis |
| Which partner categories drive engagement? | Partner engagement rate; active partner count; redemption count | Partner-category performance table with denominator and count context | Which categories to investigate for offer or partner support |
| How do new-member cohorts retain engagement? | Cohort retention rate; monthly active members | Cohort-month retention matrix and trend for fully observed periods | Whether cohort engagement patterns warrant onboarding experiments |
| Where could better reporting improve operational decisions? | All ten governed KPIs, with freshness/quality controls in later phases | Simulated stakeholder walkthrough plus transparent data-quality/coverage indicators | Identify decisions blocked by inconsistent definitions, missing eligibility history or incomplete observations |

## Scope

### In scope

- Deterministic, entirely synthetic membership, partner, offer, eligibility, event and redemption data.
- Point-in-time eligibility and activity definitions.
- Python + PostgreSQL + dbt analytics engineering, with local Power BI Desktop as the approved G4 BI path. The owner accepts the supplied report presentation as-is; Desktop operational behavior remains unverified.
- Explicit model grains, documented dimensions/facts and tests against valid and invalid fixtures.
- One Power BI report with three pages—Executive Overview, Member Engagement and Partner Performance. The supplied PDF previews show the presentation but do not evidence Windows Desktop behavior. The partner page is limited to partner/category/month grain; it does not support offer-level analysis.

### Out of scope

- Blue Light Card, other real organizations, customers, partners, systems or internal KPI definitions.
- Real member PII, scraped records, actual revenue, actual savings, operational deployment, production ownership or stakeholder interviews.
- Causal claims, experimentation results, forecasts or ROI claims without separately designed evidence.
- Paid services, internet exposure, remote publication or external account integration.

## Success criteria

The case study is successful when its synthetic inputs are reproducible; each displayed KPI has an approved-in-project definition, ownership assignment, grain, lineage and validation; the data and dbt tests detect the specified defects; BI outputs reconcile to independent reference calculations; and limitations are visible to the reader. Success is evidence of a working local portfolio artifact, not evidence of professional employment or realized business impact.

## Key assumptions and limitations

- Member status and offer-eligibility intervals are available and reliable in the synthetic source; this is a simplifying assumption, not a statement about any real company.
- One member has at most one partner-category assignment at a time; category history is not modeled in the first version.
- A qualifying member activity is a synthetic, deduplicated event from an explicitly maintained allowlist; passive page loads and unvalidated events do not automatically count.
- Offer redemptions may repeat. They must be deduplicated by source redemption identifier and validated against offer and eligibility intervals before reporting.
- Synthetic distributions are designed to exercise edge cases and plausible trends; they cannot establish real-world prevalence, causal effect or forecast accuracy.
- Partial current periods and right-censored cohorts are not compared with complete periods as if equivalent.

## Traceability

Business-question-to-KPI mapping lives above; complete KPI contracts are in [`../governance/kpi-dictionary.md`](../governance/kpi-dictionary.md), fictional ownership in [`../governance/metrics-ownership.md`](../governance/metrics-ownership.md), requirements and acceptance checks in [`requirements.md`](requirements.md), and report-evidence boundaries in [`../evidence/powerbi-acceptance-matrix.md`](../evidence/powerbi-acceptance-matrix.md).
