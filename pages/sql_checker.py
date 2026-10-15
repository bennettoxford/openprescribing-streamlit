import streamlit as st

from db import query
from utils import global_styles, sidebar_logo, sidebar_nav

st.set_page_config(layout="wide")

# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# gives navigation to other tools
sidebar_nav()

sql = st.text_area("SQL Query", height=500)

if st.button("Go"):
    try:
        result = query(sql)
        st.dataframe(result)
    except Exception as e:
        st.error(f"Query failed: {e}")
