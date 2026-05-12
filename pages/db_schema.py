import streamlit as st
from db import query

st.title("DuckDB Schema Explorer")

# Get all tables from both attached databases
tables_duckdb = query("SHOW ALL TABLES FROM duckdb_db")
tables_sqlite = query("SHOW ALL TABLES FROM sqlite_db")

for db_label, tables in [("🦆 DuckDB", tables_duckdb), ("🗃️ SQLite", tables_sqlite)]:
    st.subheader(db_label)

    if tables.empty:
        st.caption("No tables found.")
        continue

    st.caption(f"{len(tables)} tables")

    for table_name in tables["name"]:
        columns = query(f"DESCRIBE {table_name}")

        with st.expander(f"📋 {table_name}"):
            st.dataframe(
                columns[["column_name", "column_type"]],
                use_container_width=True,
                hide_index=True,
            )