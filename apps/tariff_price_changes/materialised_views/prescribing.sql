SELECT
    date,
    practice_code,
    snomed_code,
    SUM(quantity) AS quantity
FROM prescribing
WHERE date >= DATE_TRUNC('month',
        CASE
            WHEN MONTH(CURRENT_DATE) < 4
            THEN MAKE_DATE(YEAR(CURRENT_DATE) - 2, 4, 1)
            ELSE MAKE_DATE(YEAR(CURRENT_DATE) - 1, 4, 1)
        END
    )
    AND snomed_code IN (
        SELECT vpid
        FROM (
            SELECT
                date,
                vpid,
                price_in_pence,
                LAG(price_in_pence) OVER (PARTITION BY vmpp_id ORDER BY date) AS prev_price
            FROM data_tariffprice AS dt
            INNER JOIN vmpp ON dt.vmpp_id = vmpp.vppid
        )
        WHERE price_in_pence IS DISTINCT FROM prev_price
            AND date >= DATE_TRUNC('month',
                CASE
                    WHEN MONTH(CURRENT_DATE) < 4
                    THEN MAKE_DATE(YEAR(CURRENT_DATE) - 2, 4, 1)
                    ELSE MAKE_DATE(YEAR(CURRENT_DATE) - 1, 4, 1)
                END
            )
    )
GROUP BY date, practice_code, snomed_code