# dbt Lineage — Verified Local Model Graph

The graph below is the implemented dbt resource lineage. All seed data is deterministic synthetic CSV in an ignored local directory. No employer or customer source is connected.

```mermaid
flowchart LR
  subgraph RawSeeds[raw — nine local dbt seeds]
    M[members]
    SH[membership_status_history]
    PC[partner_categories]
    P[partners]
    O[offers]
    E[offer_eligibility]
    R[redemptions]
    ME[member_events]
    SP[simulation_period]
  end

  subgraph Staging[staging — typed views]
    SM[stg_members]
    SSH[stg_membership_status_history]
    SPC[stg_partner_categories]
    SPT[stg_partners]
    SO[stg_offers]
    SE[stg_offer_eligibility]
    SR[stg_redemptions]
    SME[stg_member_events]
    SSP[stg_simulation_period]
  end
  M --> SM
  SH --> SSH
  PC --> SPC
  P --> SPT
  O --> SO
  E --> SE
  R --> SR
  ME --> SME
  SP --> SSP

  SSH --> IRE[int_redemption_validation]
  SO --> IRE
  SE --> IRE
  SR --> IRE
  SSH --> IQ[int_qualifying_member_events]
  SME --> IQ
  SSP --> DD[dim_date]
  DD --> IEP[int_eligible_member_offer_period]
  SE --> IEP
  SO --> IEP
  SPT --> IEP
  SSH --> IEP

  IRE --> FR[fct_redemptions]
  SO --> DO[dim_offers]
  SPT --> DP[dim_partners]
  SPC --> DP
  SM --> DM[dim_members]

  IQ --> MME[mart_member_engagement]
  DM --> MME
  SSH --> MME
  DD --> MME
  FR --> MPP[mart_partner_performance]
  IEP --> MPP
  DP --> MPP
  MME --> MCR[mart_cohort_retention]
  MME --> MEK[mart_executive_kpis]
  MPP --> MEK
  IEP --> MEK
  FR --> MEK
```

## Operational verification

- `dbt parse`, `dbt compile`, `dbt docs generate` completed against dbt Core 1.12.6 and dbt-postgres 1.11.0.
- The generated `manifest.json` / `catalog.json` are local under ignored `dbt/target/`; the durable lineage view is this diagram plus model descriptions in `dbt/models/_models.yml` and grains in [`dbt-model-plan.md`](dbt-model-plan.md).
- `dbt build` ran twice successfully. Both builds had 21 models, 9 seeds, 120 data tests and 1 unit test pass; all nine final mart tables had matching row fingerprints across the two builds.
- The graph establishes transformation lineage only. It does not imply production lineage, external-system ownership, dashboard publication or commercial deployment.
