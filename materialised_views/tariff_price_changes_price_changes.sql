WITH price_changes AS (
SELECT
    date,
    vmpp_id,
    drug_tariff_category_id,
    price_in_pence AS price_pence,
    prev_price AS previous_price_pence,
    prev_date AS previous_date,
    prev_tariff_category
FROM (
    SELECT
    date,
    vmpp_id,
    drug_tariff_category_id,
    price_in_pence,
    LAG(price_in_pence) OVER (PARTITION BY vmpp_id ORDER BY date) AS prev_price,
    LAG(date) OVER (PARTITION BY vmpp_id ORDER BY date) AS prev_date,
    LAG(drug_tariff_category_id) OVER (PARTITION BY vmpp_id ORDER BY date) AS prev_tariff_category
    FROM data_tariffprice
)
WHERE price_in_pence IS DISTINCT FROM prev_price
    AND date = (SELECT MAX(date) FROM data_tariffprice)
ORDER BY vmpp_id, drug_tariff_category_id
),


agg_price_changes AS (
SELECT
    DATE(pc.date) AS date,
    vpid,
    CAST(pc.vmpp_id AS STRING) AS vmpp_id,
    pc.drug_tariff_category_id,
    dtcat.descr AS tariff_cat,
    pc.price_pence,
    pc.prev_tariff_category,
    prev_dtcat.descr AS prev_tariff_cat,
    pc.previous_price_pence,
    vf.nm,
    (((1 - CASE
            WHEN pc.drug_tariff_category_id IN (1, 11) THEN 0.2
            WHEN pc.drug_tariff_category_id IN (5, 6, 7, 8, 10) THEN 0.0985
            ELSE 0.05
        END) * pc.price_pence) -
    ((1 - CASE
            WHEN pc.prev_tariff_category IN (1, 11) THEN 0.2
            WHEN pc.prev_tariff_category IN (5, 6, 7, 8, 10) THEN 0.0985
            ELSE 0.05
        END) * pc.previous_price_pence)) / (vf.qtyval * 100) AS price_diff_pu
FROM price_changes pc
INNER JOIN vmpp AS vf
    ON vf.vppid = pc.vmpp_id
INNER JOIN dt_payment_category AS dtcat
    ON pc.drug_tariff_category_id = dtcat.cd
INNER JOIN dt_payment_category AS prev_dtcat
    ON pc.prev_tariff_category = prev_dtcat.cd
),

bnf_code_price_changes AS (
SELECT
    *,
    CASE 
        WHEN ROW_NUMBER() OVER (PARTITION BY vpid ORDER BY ABS(price_diff_pu) DESC) = 1
        THEN 1 
        ELSE 0
    END AS is_max_price_diff_pu
FROM agg_price_changes
)
SELECT
* FROM bnf_code_price_changes
