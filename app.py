import streamlit as st

from db import duckdb_path, query


st.title("OpenPrescribing Streamlit")

st.caption(f"Database: {duckdb_path}")

prescribing_count = query("SELECT COUNT(*) FROM prescribing")[0][0]
items_by_date = query(
    """
    SELECT date, SUM(items) AS items
    FROM prescribing
    GROUP BY date
    ORDER BY date
    """
)

st.metric("Prescribing rows", f"{prescribing_count:,}")

chart_data = {
    "date": [row[0] for row in items_by_date],
    "items": [row[1] for row in items_by_date],
}

st.subheader("Items over time")
st.line_chart(chart_data, x="date", y="items")
