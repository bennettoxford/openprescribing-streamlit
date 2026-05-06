import os
from pathlib import Path

import duckdb
import streamlit as st


data_dir = os.getenv("OPENPRESCRIBING_STREAMLIT_DATA_DIR", "data")
duckdb_path = Path(data_dir) / "prescribing.duckdb"


@st.cache_data(ttl=3600)
def query(sql):
    with duckdb.connect(duckdb_path, read_only=True) as connection:
        return connection.execute(sql).fetchall()
