import streamlit as st

pages = st.navigation(
    [
        st.Page("pages/home.py", title="Home page"),
        st.Page(
            "apps/tariff_price_changes/app.py",
            title="Tariff Price Changes",
            url_path="tariff-price-changes",
        ),
        st.Page(
            "apps/prescribing_topx/app.py",
            title="Top x Prescribing",
            url_path="prescribing-topx",
        ),
        st.Page(
            "apps/measure_aware/app.py",
            title="Measure: aWaRe",
            url_path="measure-aware",
        ),
        st.Page(
            "apps/measure_hypnotics/app.py",
            title="Measure: Hypnotics & Anxiolytics",
            url_path="measure_hypnotics",
        ),
        st.Page(
            "apps/measure_ome/app.py",
            title="Measure: Opioids OME",
            url_path="measure-ome",
        ),
        # st.Page("apps/gbg/app.py",                      title="Ghost Branded Generics",url_path="gbg"),
        st.Page(
            "apps/improvement_radar/app.py",
            title="Improvement Radar",
            url_path="improvement_radar",
        ),
        st.Page("pages/db_schema.py", title="Database schema"),
        st.Page("pages/sql_checker.py", title="Code tests"),
        st.Page("apps/growth/app.py", title="Growth", url_path="growth"),
        st.Page("apps/forecasting/app.py", title="Forecasting", url_path="forecasting"),
        st.Page(
            "apps/measure_denosumab/app.py",
            title="Measure- denosumab",
            url_path="measure_denosumab",
        ),
    ]
)


pages.run()
