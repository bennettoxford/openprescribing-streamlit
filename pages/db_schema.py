import streamlit as st
from db import query

st.title("DuckDB Schema Explorer")

# These views are created by DuckDB internally and always available
tables = query("SELECT * FROM duckdb_tables()")
columns = query("SELECT * FROM duckdb_columns()")

st.caption(f"Found {len(tables)} tables")

for _, row in tables.iterrows():
    table_name = row["table_name"]
    db_name = row["database_name"]

    table_cols = columns[columns["table_name"] == table_name][
        ["column_name", "column_type"]
    ]

    with st.expander(f"📋 {table_name} — {db_name}"):
        st.dataframe(table_cols, use_container_width=True, hide_index=True)