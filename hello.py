import streamlit as st

pages = st.navigation([
    st.Page("pages/home.py",                        title="Home page"),
    st.Page("apps/tariff_price_changes/app.py",     title="Tariff Price Changes",  url_path="tariff-price-changes"),
    st.Page("apps/prescribing_topx/app.py",         title="Top x Prescribing",     url_path="prescribing-topx"),
    st.Page("apps/measure_aware/app.py",            title="aWaRe",                 url_path="measure-aware"),
    st.Page("apps/measure_ome/app.py",              title="Opioids OME",           url_path="measure-ome"),
    st.Page("pages/db_schema.py",                   title="Database schema"),
    st.Page("pages/sql_checker.py",                 title="Code tests")
])

pages.run()