-- Read-only reference reconciliation for the governed KPI dictionary.
-- Run as lightdash_reader in a read-only, UTC, repeatable-read transaction.
-- Monthly references are independently re-aggregated from member-month,
-- partner-month, and valid-redemption grains; cohort references come from
-- member-month grain and are compared with mart_cohort_retention.
WITH member_month AS (
    SELECT
        month_start,
        bool_and(is_complete_month) AS is_complete_month,
        count(*)::numeric AS registered_members,
        count(*) FILTER (WHERE is_eligible_as_of_month_end)::numeric AS eligible_members,
        count(*) FILTER (WHERE is_active_30d_as_of_month_end)::numeric AS active_members_30d,
        count(*) FILTER (WHERE is_monthly_active)::numeric AS monthly_active_members
    FROM marts.mart_member_engagement
    GROUP BY month_start
),
partner_month AS (
    SELECT
        month_start,
        count(DISTINCT partner_id) FILTER (WHERE is_active_as_of_month_end)::numeric AS active_partners,
        count(DISTINCT partner_id) FILTER (WHERE has_available_offer)::numeric AS partners_with_offer,
        count(DISTINCT partner_id) FILTER (WHERE is_engaged_eligible_partner)::numeric AS engaged_partners,
        sum(eligible_member_offer_pairs)::numeric AS eligible_member_offer_pairs,
        sum(valid_redemption_count)::numeric AS partner_redemption_events
    FROM marts.mart_partner_performance
    GROUP BY month_start
),
redemption_month AS (
    SELECT
        date_trunc('month', redemption_date)::date AS month_start,
        count(*)::numeric AS redemption_events,
        count(DISTINCT (member_id, offer_id))::numeric AS redeemed_member_offer_pairs
    FROM marts.fct_redemptions
    GROUP BY 1
),
member_redemption_month AS (
    SELECT
        date_trunc('month', redemption_date)::date AS month_start,
        member_id,
        count(*) AS event_count
    FROM marts.fct_redemptions
    GROUP BY 1, 2
),
redemption_member_summary AS (
    SELECT
        month_start,
        count(*)::numeric AS members_with_redemption,
        count(*) FILTER (WHERE event_count >= 2)::numeric AS repeat_redeemers
    FROM member_redemption_month
    GROUP BY month_start
),
monthly_joined AS (
    SELECT
        k.month_start,
        k.month_end_date,
        k.is_complete_month,
        k.total_registered_members,
        k.eligible_members,
        k.active_members_30d,
        k.monthly_active_members,
        k.offer_redemption_count,
        k.eligible_member_offer_pairs AS executive_eligible_pairs,
        k.redeemed_member_offer_pairs,
        k.offer_redemption_rate,
        k.active_partners_as_of_month_end,
        k.partner_offer_available_count,
        k.engaged_eligible_partner_count,
        k.partner_engagement_rate,
        k.members_with_redemption,
        k.repeat_redeemers,
        k.repeat_redemption_rate,
        m.is_complete_month AS member_is_complete_month,
        m.registered_members AS ref_registered_members,
        m.eligible_members AS ref_eligible_members,
        m.active_members_30d AS ref_active_members_30d,
        m.monthly_active_members AS ref_monthly_active_members,
        p.active_partners AS ref_active_partners,
        p.partners_with_offer AS ref_partners_with_offer,
        p.engaged_partners AS ref_engaged_partners,
        p.eligible_member_offer_pairs AS ref_eligible_pairs,
        p.partner_redemption_events AS ref_partner_redemption_events,
        r.redemption_events AS ref_redemption_events,
        r.redeemed_member_offer_pairs AS ref_redeemed_pairs,
        rs.members_with_redemption AS ref_members_with_redemption,
        rs.repeat_redeemers AS ref_repeat_redeemers
    FROM marts.mart_executive_kpis k
    LEFT JOIN member_month m USING (month_start)
    LEFT JOIN partner_month p USING (month_start)
    LEFT JOIN redemption_month r USING (month_start)
    LEFT JOIN redemption_member_summary rs USING (month_start)
),
monthly_detail AS (
    SELECT
        j.month_start AS period_start,
        j.month_end_date AS period_end,
        j.is_complete_month AS actual_is_complete_month,
        j.member_is_complete_month AS reference_is_complete_month,
        v.kpi_id,
        v.kpi_name,
        v.actual_value,
        v.reference_value,
        v.actual_numerator,
        v.reference_numerator,
        v.actual_denominator,
        v.reference_denominator,
        v.reference_basis,
        v.actual_value IS NOT DISTINCT FROM v.reference_value
            AND v.actual_numerator IS NOT DISTINCT FROM v.reference_numerator
            AND v.actual_denominator IS NOT DISTINCT FROM v.reference_denominator
            AND j.is_complete_month IS NOT DISTINCT FROM j.member_is_complete_month AS matches
    FROM monthly_joined j
    CROSS JOIN LATERAL (VALUES
        ('KPI-01', 'Total registered members',
            j.total_registered_members::numeric, j.ref_registered_members,
            j.total_registered_members::numeric, j.ref_registered_members,
            NULL::numeric, NULL::numeric,
            'COUNT(*) grouped from mart_member_engagement at member-month grain'),
        ('KPI-02', 'Eligible members',
            j.eligible_members::numeric, j.ref_eligible_members,
            j.eligible_members::numeric, j.ref_eligible_members,
            NULL::numeric, NULL::numeric,
            'COUNT(*) FILTER (eligible at month end) from mart_member_engagement'),
        ('KPI-03', 'Active members (30-day)',
            j.active_members_30d::numeric, j.ref_active_members_30d,
            j.active_members_30d::numeric, j.ref_active_members_30d,
            NULL::numeric, NULL::numeric,
            'COUNT(*) FILTER (30-day active) from mart_member_engagement'),
        ('KPI-04', 'Monthly active members',
            j.monthly_active_members::numeric, j.ref_monthly_active_members,
            j.monthly_active_members::numeric, j.ref_monthly_active_members,
            NULL::numeric, NULL::numeric,
            'COUNT(*) FILTER (monthly active) from mart_member_engagement'),
        ('KPI-05', 'Offer redemption count',
            j.offer_redemption_count::numeric, COALESCE(j.ref_redemption_events, 0),
            j.offer_redemption_count::numeric, COALESCE(j.ref_redemption_events, 0),
            NULL::numeric, NULL::numeric,
            'COUNT(*) by UTC redemption_date from marts.fct_redemptions'),
        ('KPI-06', 'Offer redemption rate',
            j.offer_redemption_rate::numeric,
            COALESCE(j.ref_redeemed_pairs, 0)::numeric / NULLIF(COALESCE(j.ref_eligible_pairs, 0), 0),
            j.redeemed_member_offer_pairs::numeric, COALESCE(j.ref_redeemed_pairs, 0),
            j.executive_eligible_pairs::numeric, COALESCE(j.ref_eligible_pairs, 0),
            'Distinct member-offer pairs from fct_redemptions / summed eligible pairs from mart_partner_performance'),
        ('KPI-07', 'Active partners',
            j.active_partners_as_of_month_end::numeric, j.ref_active_partners,
            j.active_partners_as_of_month_end::numeric, j.ref_active_partners,
            NULL::numeric, NULL::numeric,
            'COUNT(DISTINCT partner_id) FILTER (active at month end) from mart_partner_performance'),
        ('KPI-08', 'Partner engagement rate',
            j.partner_engagement_rate::numeric,
            j.ref_engaged_partners / NULLIF(j.ref_partners_with_offer, 0),
            j.engaged_eligible_partner_count::numeric, j.ref_engaged_partners,
            j.partner_offer_available_count::numeric, j.ref_partners_with_offer,
            'Distinct partner counts from mart_partner_performance at partner-month grain'),
        ('KPI-09', 'Repeat redemption rate',
            j.repeat_redemption_rate::numeric,
            j.ref_repeat_redeemers / NULLIF(j.ref_members_with_redemption, 0),
            j.repeat_redeemers::numeric, j.ref_repeat_redeemers,
            j.members_with_redemption::numeric, j.ref_members_with_redemption,
            'Members grouped from marts.fct_redemptions by UTC month and member_id')
    ) AS v(kpi_id, kpi_name, actual_value, reference_value,
           actual_numerator, reference_numerator, actual_denominator,
           reference_denominator, reference_basis)
),
redemption_crosscheck AS (
    SELECT
        j.month_start AS period_start,
        j.month_end_date AS period_end,
        j.is_complete_month AS actual_is_complete_month,
        j.member_is_complete_month AS reference_is_complete_month,
        'XREF-05'::text AS kpi_id,
        'Redemption event count: partner-month vs redemption fact'::text AS kpi_name,
        COALESCE(j.ref_partner_redemption_events, 0)::numeric AS actual_value,
        COALESCE(j.ref_redemption_events, 0)::numeric AS reference_value,
        COALESCE(j.ref_partner_redemption_events, 0)::numeric AS actual_numerator,
        COALESCE(j.ref_redemption_events, 0)::numeric AS reference_numerator,
        NULL::numeric AS actual_denominator,
        NULL::numeric AS reference_denominator,
        'SUM(valid_redemption_count) from mart_partner_performance vs COUNT(*) from fct_redemptions'::text AS reference_basis,
        COALESCE(j.ref_partner_redemption_events, 0) IS NOT DISTINCT FROM COALESCE(j.ref_redemption_events, 0)
            AND j.is_complete_month IS NOT DISTINCT FROM j.member_is_complete_month AS matches
    FROM monthly_joined j
),
cohort_reference AS (
    SELECT
        cohort_month,
        ((extract(year FROM month_start) - extract(year FROM cohort_month)) * 12
          + extract(month FROM month_start) - extract(month FROM cohort_month))::integer AS age_month,
        bool_and(is_complete_month) AS is_complete_month,
        count(DISTINCT member_id)::numeric AS cohort_size,
        count(DISTINCT member_id) FILTER (
            WHERE is_monthly_active AND is_complete_month
        )::numeric AS retained_members
    FROM marts.mart_member_engagement
    GROUP BY cohort_month, month_start
),
cohort_detail AS (
    SELECT
        (c.cohort_month + (c.age_month * interval '1 month'))::date AS period_start,
        ((c.cohort_month + (c.age_month * interval '1 month'))::date + interval '1 month - 1 day')::date AS period_end,
        t.is_complete_month AS actual_is_complete_month,
        c.is_complete_month AS reference_is_complete_month,
        'KPI-10'::text AS kpi_id,
        'Cohort retention rate'::text AS kpi_name,
        t.cohort_retention_rate::numeric AS actual_value,
        CASE WHEN c.is_complete_month
             THEN c.retained_members / NULLIF(c.cohort_size, 0)
             ELSE NULL::numeric
        END AS reference_value,
        t.retained_members::numeric AS actual_numerator,
        c.retained_members AS reference_numerator,
        t.cohort_size::numeric AS actual_denominator,
        c.cohort_size AS reference_denominator,
        'Recomputed from mart_member_engagement grouped by registration cohort and relative calendar month'::text AS reference_basis,
        t.cohort_retention_rate::numeric IS NOT DISTINCT FROM
            CASE WHEN c.is_complete_month
                 THEN c.retained_members / NULLIF(c.cohort_size, 0)
                 ELSE NULL::numeric
            END
            AND t.retained_members::numeric IS NOT DISTINCT FROM c.retained_members
            AND t.cohort_size::numeric IS NOT DISTINCT FROM c.cohort_size
            AND t.is_complete_month IS NOT DISTINCT FROM c.is_complete_month AS matches
    FROM marts.mart_cohort_retention t
    JOIN cohort_reference c USING (cohort_month, age_month)
)
SELECT * FROM monthly_detail
UNION ALL
SELECT * FROM redemption_crosscheck
UNION ALL
SELECT * FROM cohort_detail
ORDER BY period_start, kpi_id, kpi_name;
