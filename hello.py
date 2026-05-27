import streamlit as st

pages = st.navigation([
    st.Page("pages/home.py", title="Home page"),
    st.Page("apps/tariff_price_changes/tariff_price_changes.py", title="Tariff Price Changes"),
    st.Page("apps/prescribing_topx/prescribing_topx.py", title="Top x Prescribing"),
    st.Page("apps/measure_aware/measure_aware.py", title="aWaRe"),
    st.Page("apps/opioids_ome/opioids_ome.py", title="Ooioids OME"),
    st.Page("pages/db_schema.py", title="Database schema"),
    st.Page("pages/sql_checker.py", title="Code tests")
])

pages.run()
