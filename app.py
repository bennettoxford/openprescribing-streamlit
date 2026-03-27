import os

import duckdb
import streamlit as st


DUCKDB_PATH_ENV_VAR = "DUCKDB_PATH"


@st.cache_data(ttl=3600)
def get_dashboard_data(duckdb_path: str) -> tuple[int, list[tuple[object, object]]]:
    with duckdb.connect(duckdb_path, read_only=True) as connection:
        prescribing_count = connection.execute("SELECT COUNT(*) FROM prescribing").fetchone()[0]
        items_by_date = connection.execute(
            """
            SELECT date, SUM(items) AS items
            FROM prescribing
            GROUP BY date
            ORDER BY date
            """
        ).fetchall()

    return prescribing_count, items_by_date


st.title("OpenPrescribing Streamlit")

duckdb_path = os.getenv(DUCKDB_PATH_ENV_VAR)

if not duckdb_path:
    st.error(f"Set the {DUCKDB_PATH_ENV_VAR} environment variable to a DuckDB database path.")
    st.stop()

st.caption(f"Database: {duckdb_path}")

try:
    prescribing_count, items_by_date = get_dashboard_data(duckdb_path)
except Exception as exc:
    st.error(f"Query failed: {exc}")
    st.stop()

st.metric("Prescribing rows", f"{prescribing_count:,}")

chart_data = {
    "date": [row[0] for row in items_by_date],
    "items": [row[1] for row in items_by_date],
}

st.subheader("Items over time")
st.line_chart(chart_data, x="date", y="items")
