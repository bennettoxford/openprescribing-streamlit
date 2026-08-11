WITH base AS (
    SELECT
        practice_code,
        substr(bnf_code, 1, 7) AS subpara,
        date,
        SUM(actual_cost) AS actual_cost,
        SUM(items)       AS items
    FROM prescribing
    WHERE date >= DATE '2022-05-01'
    GROUP BY
        practice_code,
        substr(bnf_code, 1, 7),
        date
),
w AS (
    SELECT
        date,
        practice_code,
        subpara,
        SUM(actual_cost) OVER win_12   AS spend_last_12m,
        SUM(actual_cost) OVER win_prev AS spend_prev_12m,
        SUM(items)       OVER win_12   AS items_last_12m,
        SUM(items)       OVER win_prev AS items_prev_12m
    FROM base
    WINDOW
        base_win AS (PARTITION BY practice_code, subpara ORDER BY date),
        win_12   AS (base_win ROWS BETWEEN 11 PRECEDING AND CURRENT ROW),
        win_prev  AS (base_win ROWS BETWEEN 23 PRECEDING AND 12 PRECEDING)
)
SELECT *
FROM w
WHERE date >= DATE '2024-04-01';