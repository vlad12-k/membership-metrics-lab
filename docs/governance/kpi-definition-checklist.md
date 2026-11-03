# KPI Contract Review Checklist

Use this checklist when adding or changing a governed metric. A metric is not ready for publication until the applicable fields are completed in `kpi-dictionary.md` and verified against models/tests.

- [ ] Name and business description are unambiguous.
- [ ] Formula states aggregation and non-additive behavior.
- [ ] Numerator and denominator are defined separately, or denominator is marked not applicable.
- [ ] Grain and dimensions are explicit.
- [ ] Time window and date attribution are explicit, including timezone and boundaries.
- [ ] Eligible and excluded populations are defined.
- [ ] NULL, zero-denominator, duplicate and invalid-record treatment is documented.
- [ ] Fictional business owner, steward and technical maintainer are identified without inventing real approvals.
- [ ] Sources, dbt models, metric metadata and downstream reports are traceable.
- [ ] Known limitations are visible.
- [ ] Unit/business tests cover representative boundaries and a failure case.
- [ ] Independent reconciliation example passes.
- [ ] Version/change history and downstream impact are recorded.
