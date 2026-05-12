import pandas as pd
import streamlit as st

from db import query

st.title("DuckDB Schema Explorer")

tables = query("""
    SELECT table_name, database_name, 'table' AS kind
    FROM duckdb_tables()
    WHERE database_name != 'system'
""")

views = query("""
    SELECT view_name AS table_name, database_name, 'view' AS kind
    FROM duckdb_views()
    WHERE database_name != 'system'
""")

all_tables = pd.concat([tables, views], ignore_index=True)
columns = query("SELECT * FROM duckdb_columns()")

st.caption(f"Found {len(all_tables)} tables/views")

icons = {"table": "📋", "view": "👁️"}

for _, row in all_tables.iterrows():
    table_name = row["table_name"]
    db_name = row["database_name"]
    kind = row["kind"]

    if kind == "table":
        table_cols = columns[columns["table_name"] == table_name][
            ["column_name", "data_type"]
        ]
    else:
        try:
            empty = query(f"SELECT * FROM {table_name} LIMIT 0")
            table_cols = pd.DataFrame({
                "column_name": empty.columns.tolist(),
                "data_type": [str(dt) for dt in empty.dtypes],
            })
        except Exception as e:
            table_cols = pd.DataFrame({"column_name": [f"Error: {e}"], "data_type": [""]})

    with st.expander(f"{icons[kind]} {table_name} — {db_name} ({kind})"):
        st.dataframe(table_cols, use_container_width=True, hide_index=True)