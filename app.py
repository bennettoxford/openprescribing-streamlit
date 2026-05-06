import streamlit as st

from db import duckdb_path, query


st.title("OpenPrescribing Streamlit")

st.caption(f"Database: {duckdb_path}")

prescribing_count = query("SELECT COUNT(*) FROM prescribing").iat[0, 0]
items_by_date = query(
    """
    SELECT date, SUM(items) AS items
    FROM prescribing
    GROUP BY date
    ORDER BY date
    """
)

st.metric("Prescribing rows", f"{prescribing_count:,}")

st.subheader("Items over time")
st.line_chart(items_by_date, x="date", y="items")
