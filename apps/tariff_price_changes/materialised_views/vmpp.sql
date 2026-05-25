SELECT
DATE(date) as date,
nm,
vpid,
vmpp_id,
tariff_category,
price_pence,
prev_price AS previous_price_pence,
DATE(prev_date) AS previous_date,
prev_tariff_category,
CASE 
    WHEN price_pence > prev_price THEN 'increase'
    WHEN price_pence < prev_price THEN 'decrease'
    ELSE 'unchanged'
END AS price_change
FROM (
SELECT
    date,
    nm,
    vmpp_id,
    vpid,
    dtcat.descr AS tariff_category,
    price_in_pence AS price_pence,
    LAG(price_in_pence) OVER (PARTITION BY vmpp ORDER BY date) AS prev_price,
    LAG(date) OVER (PARTITION BY vmpp ORDER BY date) AS prev_date,
    LAG(dtcat.descr) OVER (PARTITION BY vmpp ORDER BY date) AS prev_tariff_category
FROM data_tariffprice AS tariff
INNER JOIN vmpp
    ON vmpp.vppid = tariff.vmpp_id
INNER JOIN dt_payment_category AS dtcat
    ON tariff.drug_tariff_category_id = dtcat.cd
)
WHERE date >= DATE_TRUNC('month',
    CASE
        WHEN MONTH(CURRENT_DATE) < 4
        THEN MAKE_DATE(YEAR(CURRENT_DATE) - 2, 4, 1)
        ELSE MAKE_DATE(YEAR(CURRENT_DATE) - 1, 4, 1)
    END
)
ORDER BY vmpp_id, tariff_category