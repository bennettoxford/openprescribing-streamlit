import streamlit as st
from db import query

st.title("DuckDB Schema Explorer")

for db_label, db_name in [("🦆 DuckDB", "duckdb_db"), ("🗃️ SQLite", "sqlite_db")]:
    st.subheader(db_label)

    tables = query(f"""
        SELECT table_name
        FROM {db_name}.information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """)

    if tables.empty:
        st.caption("No tables found.")
        continue

    st.caption(f"{len(tables)} tables")

    for table_name in tables["table_name"]:
        columns = query(f"""
            SELECT column_name, data_type
            FROM {db_name}.information_schema.columns
            WHERE table_schema = 'main'
              AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """)

        with st.expander(f"📋 {table_name}"):
            st.dataframe(
                columns,
                use_container_width=True,
                hide_index=True,
            )