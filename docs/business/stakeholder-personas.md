# Simulated Stakeholder Personas

**Important:** These fictional personas were designed for requirements analysis. They are not real people, were not interviewed and do not imply workplace discovery.

| Persona | Objective and decision | Required metrics | Cadence and filters | Ambiguities to resolve | Data-quality risks |
|---|---|---|---|---|---|
| Head of Analytics | Maintain trusted shared measures; decide whether a reported movement is reliable enough to share | Registered/eligible/active members, redemption rate, partner engagement, freshness and quality status | Monthly; reporting period, membership state, category, partner | What “active” means; point-in-time versus period-to-date; shared denominator | Metric drift; incorrect date attribution; duplicate joins; incomplete history |
| Marketing Manager | Assess member engagement and identify cohorts or categories for investigation; choose where to test campaign ideas | Monthly active members, redemption rate, cohort retention, new versus returning | Weekly monitoring and monthly review; cohort, category, period, eligibility | Is a redemption rate based on eligible people or eligible offers? Are incomplete cohorts comparable? | Missing eligibility snapshots; duplicated events; campaign exposure not modeled; correlation mistaken for lift |
| Partnerships Manager | Understand partner availability and engagement; prioritize a review of offers or categories | Active partners, partner engagement rate, valid redemptions, repeat redemptions | Monthly; partner, category, offer, validity window | Does “active partner” mean contracted, active on platform, or with a valid offer? | Expired offers; partner status timing; category assignment gaps; invalid/out-of-window redemptions |
| Finance Analyst | Reconcile operational reporting and assess engagement inputs to planning; not infer revenue from this dataset | Valid redemption count, eligible population, repeat redemption, partner engagement | Monthly close-like snapshot; date, partner, category | Count of redemption transactions versus member-offer pairs; simulated amounts versus actual finance | Duplicated transactions; refunds/reversals not modeled; no revenue or settlement source |
| Operations Manager | Detect data-quality or availability issues that block reporting; decide whether an output should be held or annotated | Freshness, source/target counts, rejected records, active members, eligibility coverage | Daily quality check and monthly report; source/run date, status, category | When to warn, quarantine or fail; zero versus unknown denominator | Late data; failed ingestion; malformed records; silent drop; zero/NULL confusion |

## Persona constraints

- These personas are analytical design aids, not actual stakeholders or requirements gathered in employment.
- Filters are proposed UX needs and must not alter KPI semantics without an explicit rule.
- Report audiences do not obtain data access merely because a persona is described; security controls remain a separate design concern.
- No simulated persona should be described as a user who tested or approved the project.
