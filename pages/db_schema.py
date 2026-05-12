import duckdb
import streamlit as st

DB_PATH = "data/prescribing.duckdb"  # update this

st.title("DuckDB Schema Explorer")

try:
    con = duckdb.connect(DB_PATH, read_only=True)

    tables = con.execute("SHOW TABLES").fetchdf()

    if tables.empty:
        st.warning("No tables found in database.")
    else:
        st.caption(f"Found **{len(tables)}** tables")

        for table_name in tables["name"]:
            columns = con.execute(f"DESCRIBE {table_name}").fetchdf()

            with st.expander(f"📋 {table_name}"):
                st.dataframe(
                    columns[["column_name", "column_type"]],
                    use_container_width=True,
                    hide_index=True,
                )

    con.close()

except Exception as e:
    st.error(f"Could not connect to database: {e}")