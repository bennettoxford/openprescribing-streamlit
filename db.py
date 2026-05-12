import os
from pathlib import Path

import duckdb
import streamlit as st


data_dir = Path(os.getenv("OPENPRESCRIBING_STREAMLIT_DATA_DIR", "data")).expanduser()
duckdb_path = data_dir / "prescribing.duckdb"
sqlite_path = data_dir / "data.sqlite"
create_views_sql = (Path(__file__).parent / "create_views.sql").read_text()


@st.cache_data(ttl=3600)
def query(sql, dfs: dict = None): # now includes dfs connection so that we can attached filter to it
    with duckdb.connect() as connection:
        connection.execute(
            f"""
            ATTACH {_escape(duckdb_path)} AS duckdb_db (TYPE DUCKDB, READ_ONLY);
            ATTACH {_escape(sqlite_path)} AS sqlite_db (TYPE SQLITE, READ_ONLY);
            """
        )
        connection.execute("SET enable_external_access = false")
        connection.execute("SET search_path = 'memory,sqlite_db,duckdb_db'")
        connection.execute(create_views_sql)
        if dfs:
            for name, df in dfs.items():
                connection.register(name, df)
        return connection.execute(sql).df()


def _escape(value):
    # DuckDB doesn't accept parameter placeholders for filenames in queries so we have
    # to escape them manually.
    return "'" + str(value).replace("'", "''") + "'"

