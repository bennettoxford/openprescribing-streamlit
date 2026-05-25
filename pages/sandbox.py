
import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
from db import query, create_materialised_view
from datetime import datetime

from org_filter import org_filter_sidebar

st.set_page_config(layout="wide")

max_rx_date = query("SELECT MAX(date) FROM date")["max(date)"][0]
max_tariff_date = query("SELECT MAX(date) FROM data_tariffprice")["max(date)"][0]
tariff_month = max_tariff_date.strftime('%B %Y')
rx_month = max_rx_date.strftime('%B %Y')

st.write(tariff_month)
st.write(rx_month)




#test_rx = query(
 #   """
 #   SELECT
 #   rx.practice_code,  
 #   med.name,
  #  rx.snomed_code,
 #   SUM(rx.quantity_value) as quantity
 #   FROM prescribing as rx
 #   INNER JOIN
#    medications AS med
#    ON
 #   rx.snomed_code = med.id
 #   WHERE date = (SELECT MAX(date) FROM date)
#   GROUP BY rx.practice_code, med.name, rx.snomed_code
 #   """)



create_materialised_view(name="prescribing_2025")

test_query = query(
    """
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
    AND date >= DATE_TRUNC('month',
        CASE
            WHEN MONTH(CURRENT_DATE) < 4
            THEN MAKE_DATE(YEAR(CURRENT_DATE) - 2, 4, 1)
            ELSE MAKE_DATE(YEAR(CURRENT_DATE) - 1, 4, 1)
        END
    )
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
            WHEN ROW_NUMBER() OVER (PARTITION BY vpid, date ORDER BY ABS(price_diff_pu) DESC) = 1
            THEN 1 
            ELSE 0
        END AS is_max_price_diff_pu
    FROM agg_price_changes
    )
    SELECT * FROM bnf_code_price_changes
    """
)

st.dataframe(test_query)