import streamlit as st

pages = st.navigation([
    st.Page("pages/home.py", title="Home page"),
    st.Page("pages/tariff_price_changes.py", title="Tariff Price Changes"),
    st.Page("pages/prescribing_topx.py", title="Top x Prescribing"),
    #st.Page("pages/opioids.py", title="Opioids measures"),
])

pages.run()
