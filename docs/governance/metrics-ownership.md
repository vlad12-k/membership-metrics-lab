# Metrics Ownership and Governance

**Scope:** Simulated ownership for fictional MemberLoop only. These roles and assignments are invented; no real stakeholders were interviewed or consulted.

## Accountability model

- **Metric owner:** fictional business role accountable for the metric's meaning and decision use; proposes semantic changes and approves the business rationale within the case study.
- **Steward:** Head of Analytics, responsible for consistent definition, source-to-report lineage, quality controls, documentation, review of changes and preventing duplicate/conflicting measures.
- **Technical maintainer:** project implementation (Vladyslav Kononov, portfolio author), responsible for code/tests and documenting actual technical behavior; this is not a claim of organizational production ownership.
- **Consumer:** simulated stakeholder persona; may use published metrics but does not redefine them through a local visual calculation.

## Ownership register

| KPI | Fictional business owner | Steward | Technical maintainer | Review cadence | Intended decision |
|---|---|---|---|---|---|
| Total registered members | Head of Analytics | Head of Analytics | Project implementation | Quarterly or definition change | Understand cumulative registered population |
| Eligible members | Operations Manager | Head of Analytics | Project implementation | Monthly or status-rule change | Understand active member population at a date |
| Active members (30-day) | Marketing Manager | Head of Analytics | Project implementation | Monthly or event allowlist change | Review recent engagement |
| Monthly active members | Marketing Manager | Head of Analytics | Project implementation | Monthly | Review activity trend |
| Offer redemption count | Partnerships Manager | Head of Analytics | Project implementation | Monthly or redemption-rule change | Review valid redemption volume |
| Offer redemption rate | Marketing Manager | Head of Analytics | Project implementation | Monthly or denominator change | Compare eligible offer opportunities with redemptions |
| Active partner count | Partnerships Manager | Head of Analytics | Project implementation | Monthly or partner-status change | Review active partner population |
| Partner engagement rate | Partnerships Manager | Head of Analytics | Project implementation | Monthly or offer-availability change | Review partners with eligible opportunity and redemption |
| Repeat redemption rate | Finance Analyst | Head of Analytics | Project implementation | Monthly or repeat rule change | Understand repeated valid events, not revenue |
| Cohort retention rate | Marketing Manager | Head of Analytics | Project implementation | Monthly or cohort/activity change | Review cohort engagement pattern |

## Definition-change workflow

1. Record the business question and requested change in the decision log.
2. Identify dependent sources, models, measures, filters, reports and reconciliation tests.
3. Compare current and proposed grain, population, event/status rules, numerator, denominator, time basis and NULL treatment.
4. Obtain simulated owner/steward approval in the project decision record; never imply approval by actual stakeholders.
5. Implement a versioned change with tests and an effective date; document impact and migration where a consumer definition changes.
6. Reconcile current versus proposed results on selected reference cases and a historical slice.
7. Update the KPI dictionary, model documentation, lineage, reports and status evidence together.
8. Publish only after project gates pass and G6 is explicitly authorized by the owner.

## Controls

- One canonical definition per KPI name; materially different definitions get distinct names.
- No KPI formula is hidden solely in a chart-level calculation.
- Denominator changes are treated as semantic breaking changes.
- Historical restatement behavior is explicit; v1 has no automatic restatement policy.
- Missing data is not silently converted to zero; a zero denominator returns not-defined.
- Project artifacts must distinguish simulated ownership from actual employment or stakeholder sign-off.
