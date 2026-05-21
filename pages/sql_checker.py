import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
from db import query



st.set_page_config(layout="wide")

sql = st.text_area("SQL Query", height=250)

if st.button("Go"):
    try:
        result = query(sql)
        st.dataframe(result)
    except Exception as e:
        st.error(f"Query failed: {e}")