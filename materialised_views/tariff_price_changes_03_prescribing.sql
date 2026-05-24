SELECT
    practice_code,
    snomed_code,
    SUM(quantity) AS quantity
FROM prescribing
WHERE date = (SELECT MAX(date) FROM prescribing)
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
            AND date = (SELECT MAX(date) FROM data_tariffprice)
    )
GROUP BY practice_code, snomed_code
