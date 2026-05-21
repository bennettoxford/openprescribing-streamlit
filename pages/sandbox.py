
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

test_matview = query(
    """
    SELECT * from prescribing_2025
    LIMIT 200
    """
)

st.dataframe(test_matview)