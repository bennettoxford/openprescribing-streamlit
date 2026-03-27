import os

import duckdb
import streamlit as st


DUCKDB_PATH_ENV_VAR = "DUCKDB_PATH"

st.title("OpenPrescribing Streamlit")

duckdb_path = os.getenv(DUCKDB_PATH_ENV_VAR)

if not duckdb_path:
    st.error(f"Set the {DUCKDB_PATH_ENV_VAR} environment variable to a DuckDB database path.")
    st.stop()

st.caption(f"Database: {duckdb_path}")

try:
    with duckdb.connect(duckdb_path, read_only=True) as connection:
        prescribing_count = connection.execute("SELECT COUNT(*) FROM prescribing").fetchone()[0]
except Exception as exc:
    st.error(f"Query failed: {exc}")
    st.stop()

st.metric("Prescribing rows", f"{prescribing_count:,}")
