import altair as alt
import streamlit as st
import pandas as pd

from db import duckdb_path, query

st.set_page_config(layout="wide")

st.title("OpenPrescribing Top 20 prescribing by items in 2025")


df_region = query(
    """
    SELECT
    org.id AS id, org.name AS name
    FROM org
    WHERE org.org_type = 'reg'
    """
)

df_icb = query(
    """
    SELECT
    org.id AS id, org.name AS name
    FROM org
    WHERE org.org_type = 'icb'
    """
)

df_pcn = query(
    """
    SELECT
    org.id AS id, org.name AS name
    FROM org
    WHERE org.org_type = 'pcn'
    """
)

df_practice = query(
    """
    SELECT
        p.id AS practice_code,
        p.name AS practice_name,
        MAX(CASE WHEN anc.org_type = 'pcn' THEN anc.id END) AS pcn_code,
        MAX(CASE WHEN anc.org_type = 'pcn' THEN anc.name END) AS pcn_name,
        MAX(CASE WHEN anc.org_type = 'icb' THEN anc.id END) AS icb_code,
        MAX(CASE WHEN anc.org_type = 'icb' THEN anc.name END) AS icb_name,
        MAX(CASE WHEN anc.org_type = 'reg' THEN anc.id END) AS region_code,
        MAX(CASE WHEN anc.org_type = 'reg' THEN anc.name END) AS region_name
    FROM org p
    INNER JOIN org_relation rel ON p.id = rel.child_id
    INNER JOIN org anc ON rel.parent_id = anc.id
    WHERE p.org_type = 'pra'
    AND p.inactive = 0
    GROUP BY p.id, p.name
    """
)

def cascading_filter(df, col, label, key):
    opts = sorted(df[col].dropna().unique().tolist())
    sel = [v for v in st.session_state.get(key, []) if v in opts]
    sel = st.multiselect(label, opts, default=sel, key=key)
    return df if not sel else df[df[col].isin(sel)]

# --- Sidebar filters ---
with st.sidebar:

    st.header("Organisation Filter")
    st.info("Select an organisation at any level.")

    df_region   = cascading_filter(df_practice, "region_name",   "Region",   "sel_region")
    df_icb      = cascading_filter(df_region,    "icb_name",      "ICB",      "sel_icb")
    df_pcn      = cascading_filter(df_icb,       "pcn_name",      "PCN",      "sel_pcn")
    df_selected = cascading_filter(df_pcn,       "practice_name", "Practice", "sel_practice")

    selected_practice_codes = df_selected["practice_code"].unique().tolist()

df_topx = query(
    """
    SELECT
        vtm.nm AS name,
        sum(items) as items
    from prescribing AS rx
    inner join
    medications as med
    ON
    rx.snomed_code = med.id
    inner join
    vtm AS vtm
    ON
    med.vtm_id = vtm.vtmid
    INNER JOIN _selected_practices AS s
      ON rx.practice_code = s.practice_code
    WHERE
    date between '2025-01-01' and '2025-12-01'
    GROUP BY vtm.nm
    ORDER BY sum(items)DESC
    LIMIT 20
""", 
dfs={"_selected_practices": pd.DataFrame({"practice_code": selected_practice_codes})}
)

st.dataframe(df_topx)