WITH orgs AS (
    SELECT
        prac.id AS practice_code,
        MAX(CASE WHEN par.org_type = 'pcn' THEN par.id END) AS pcn_code,
        MAX(CASE WHEN par.org_type = 'icb' THEN par.id END) AS icb_code,
        MAX(CASE WHEN par.org_type = 'reg' THEN par.id END) AS region_code
    FROM org AS prac
    INNER JOIN org_relation AS rel ON prac.id = rel.child_id
    INNER JOIN org AS par ON rel.parent_id = par.id
    WHERE prac.org_type = 'pra'
    AND prac.inactive = 0
    GROUP BY prac.id
),
base AS (
    SELECT
        orgs.practice_code,
        orgs.pcn_code,
        orgs.icb_code,
        orgs.region_code,
        substr(prescribing.bnf_code, 1, 7) AS subpara,
        date,
        SUM(actual_cost) AS actual_cost,
        SUM(items)       AS items
    FROM prescribing
    INNER JOIN orgs ON orgs.practice_code = prescribing.practice_code
    WHERE date >= DATE '2022-05-01'
    GROUP BY
        orgs.practice_code,
        orgs.pcn_code,
        orgs.icb_code,
        orgs.region_code,
        substr(prescribing.bnf_code, 1, 7),
        date
),
grouped AS (
    SELECT
        date,
        practice_code,
        pcn_code,
        icb_code,
        region_code,
        subpara,
        SUM(actual_cost) AS actual_cost,
        SUM(items)       AS items
    FROM base
    GROUP BY GROUPING SETS (
        (date, practice_code, pcn_code, icb_code, region_code, subpara),
        (date, pcn_code, subpara),
        (date, icb_code, subpara),
        (date, region_code, subpara),
        (date, subpara)
    )
),
w AS (
    SELECT
        date,
        practice_code,
        pcn_code,
        icb_code,
        region_code,
        subpara,
        SUM(actual_cost) OVER win_12   AS spend_last_12m,
        SUM(actual_cost) OVER win_prev AS spend_prev_12m,
        SUM(items)       OVER win_12   AS items_last_12m,
        SUM(items)       OVER win_prev AS items_prev_12m
    FROM grouped
    WINDOW
        base_win AS (
            PARTITION BY practice_code, pcn_code, icb_code, region_code, subpara
            ORDER BY date
        ),
        win_12   AS (base_win ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
        win_prev AS (base_win ROWS BETWEEN 23 PRECEDING AND 12 PRECEDING)
)
SELECT *
FROM w
WHERE date >= DATE '2024-04-01'