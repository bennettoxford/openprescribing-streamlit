import os
from pathlib import Path

import duckdb
import streamlit as st

BASE_DIR = Path(__file__).parent
APPS_DIR = BASE_DIR / "apps"

data_dir = Path(os.getenv("OPENPRESCRIBING_STREAMLIT_DATA_DIR", "data")).expanduser()
prescribing_db_path = data_dir / "prescribing.duckdb"
sqlite_path = data_dir / "data.sqlite"
materialised_views_db_path = data_dir / "materialised_views.duckdb"
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
            ATTACH {_escape(materialised_views_db_path)} AS materialised_views_db (TYPE DUCKDB, READ_WRITE);
            """
        )
        connection.execute(
            "SET search_path = 'materialised_views_db,memory,sqlite_db,prescribing_db'"
        )

    else:
        connection.execute(
            f"""
            ATTACH {_escape(materialised_views_db_path)} AS materialised_views_db (TYPE DUCKDB, READ_ONLY);
            """
        )
        connection.execute(
            "SET search_path = 'memory,sqlite_db,prescribing_db,materialised_views_db'"
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


def recreate_materialised_views():
    print("Removing all materialised views")
    if materialised_views_db_path.exists():
        materialised_views_db_path.unlink()

    print("Creating all materialised views")
    for app_dir in sorted(APPS_DIR.iterdir()):
        if not app_dir.is_dir():
            continue

        app_file = app_dir / "app.py"
        materialised_views_dir = app_dir / "materialised_views"

        if not materialised_views_dir.is_dir():
            continue

        for f in sorted(materialised_views_dir.iterdir()):
            short_name = f.name.removesuffix(".sql")
            print(f"Creating materialised view {short_name}")
            create_materialised_view(
                short_name,
                app_file,
                app_dir.name,
                force=True,
            )

    print("All materialised views (re-)created")


@st.cache_data
def create_materialised_view(name, app_file, tool_name, max_age_hours=168, force=False):
    materialised_views_dir = Path(app_file).parent / "materialised_views"
    sql = (materialised_views_dir / f"{name}.sql").read_text()
    full_name = f"{tool_name}_{name}"

    data_dir = Path(app_file).parent / "csvs" # allows csvs stored in `data` to be used
    sql = sql.replace('{data_dir}', str(data_dir))

    with duckdb.connect() as connection:
        attach_prescribing_and_sqlite_dbs(connection)
        attach_materialised_views_db(connection, read_write=True)

        if not force:
            try:
                result = connection.execute(f"""
                    SELECT (NOW() - MAX(created_at)) < INTERVAL '{max_age_hours} hours'
                    FROM {full_name}_meta
                """).fetchone()

                if result and result[0]:
                    return

            except Exception:
                pass

        connection.execute(f"CREATE OR REPLACE TABLE {full_name} AS {sql}")
        connection.execute(f"""
            CREATE OR REPLACE TABLE {full_name}_meta AS
            SELECT NOW() AS created_at
        """)
