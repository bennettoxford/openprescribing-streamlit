import os
from pathlib import Path

import duckdb
import streamlit as st

data_dir = Path(os.getenv("OPENPRESCRIBING_STREAMLIT_DATA_DIR", "data")).expanduser()
prescribing_db_path = data_dir / "prescribing.duckdb"
sqlite_path = data_dir / "data.sqlite"
materialised_views_db_path = data_dir / "materalised_views.duckdb"
materialised_views_dir = Path(__file__).parent / "materialised_views"
create_views_sql = (Path(__file__).parent / "create_views.sql").read_text()


def attach_prescribing_and_sqlite_dbs(connection):
    connection.execute(
        f"""
        ATTACH {_escape(prescribing_db_path)} AS prescribing_db (TYPE DUCKDB, READ_ONLY);
        ATTACH {_escape(sqlite_path)} AS sqlite_db (TYPE SQLITE, READ_ONLY);
        """
    )
    connection.execute("SET search_path = 'memory,sqlite_db,prescribing_db'")
    connection.execute(create_views_sql)


def attach_materialised_views_db(connection, read_write=True):
    if read_write:
        connection.execute(
            f"""
            ATTACH {_escape(materialised_views_db_path)} AS materalised_views_db (TYPE DUCKDB, READ_WRITE);
            """
        )
        connection.execute(
            "SET search_path = 'materalised_views_db,memory,sqlite_db,prescribing_db'"
        )

    else:
        connection.execute(
            f"""
            ATTACH {_escape(materialised_views_db_path)} AS materalised_views_db (TYPE DUCKDB, READ_ONLY);
            """
        )
        connection.execute(
            "SET search_path = 'memory,sqlite_db,prescribing_db,materalised_views_db'"
        )


@st.cache_data(ttl=3600)
def query(
    sql, dfs: dict = None
):  # now includes dfs connection so that we can attached filter to it
    with duckdb.connect() as connection:
        attach_prescribing_and_sqlite_dbs(connection)
        if materialised_views_db_path.exists():
            attach_materialised_views_db(connection, read_write=False)

        connection.execute("SET enable_external_access = false")

        if dfs:
            for name, df in dfs.items():
                connection.register(name, df)
        return connection.execute(sql).df()


def _escape(value):
    # DuckDB doesn't accept parameter placeholders for filenames in queries so we have
    # to escape them manually.
    return "'" + str(value).replace("'", "''") + "'"


def create_materialised_view(name, max_age_hours=168):
    sql = (materialised_views_dir / f"{name}.sql").read_text()

    with duckdb.connect() as connection:
        attach_prescribing_and_sqlite_dbs(connection)
        attach_materialised_views_db(connection, read_write=True)

        try:
            result = connection.execute(f"""
                SELECT (NOW() - MAX(created_at)) < INTERVAL '{max_age_hours} hours'
                FROM {name}_meta
            """).fetchone()
            if result and result[0]:
                return
        except Exception:
            pass

        connection.execute(f"CREATE OR REPLACE TABLE {name} AS {sql}")
        connection.execute(f"""
            CREATE OR REPLACE TABLE {name}_meta AS
            SELECT NOW() AS created_at
        """)
