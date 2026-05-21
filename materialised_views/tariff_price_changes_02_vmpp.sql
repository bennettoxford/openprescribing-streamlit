SELECT
DATE(date) as date,
nm,
vpid,
vmpp_id,
tariff_category,
price_pence,
prev_price AS previous_price_pence,
DATE(prev_date) AS previous_date,
prev_tariff_category
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
WHERE date = (SELECT MAX(date) FROM data_tariffprice)
ORDER BY vmpp_id, tariff_category