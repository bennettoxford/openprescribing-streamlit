import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from db import agg_path, build_agg, duckdb_path, query

st.set_page_config(layout="wide")

st.title("OpenPrescribing Top 20 prescribing in 2025")

st.markdown(
    """
<style>
[data-testid="stDataFrame"] td { border: none !important; }
</style>
""",
    unsafe_allow_html=True,
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

build_agg(
    table_name="prescribing_agg",
    sql="""
        SELECT
            rx.practice_code as practice_code,
            med.vtm_id AS vtm_id,
            vtm.nm AS vtm_name,
            med.id AS snomed_code,
            med.name AS pres_name,
            SUM(rx.items) AS items,
            SUM(rx.actual_cost) AS actual_cost
        FROM prescribing rx
        JOIN medications med ON rx.snomed_code = med.id
        JOIN vtm vtm ON med.vtm_id = vtm.vtmid
        WHERE rx.date BETWEEN '2025-01-01' AND '2025-12-01'
        GROUP BY rx.practice_code, med.vtm_id, vtm.nm, med.id, med.name
    """,
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

    df_region = cascading_filter(df_practice, "region_name", "Region", "sel_region")
    df_icb = cascading_filter(df_region, "icb_name", "ICB", "sel_icb")
    df_pcn = cascading_filter(df_icb, "pcn_name", "PCN", "sel_pcn")
    df_selected = cascading_filter(df_pcn, "practice_name", "Practice", "sel_practice")

    selected_practice_codes = df_selected["practice_code"].unique().tolist()

    top_n = st.slider("Top N items", min_value=5, max_value=100, value=20)
    sort_by = st.radio("Sort by", ["Cost", "Items"], horizontal=True)

sort_col = "actual_cost" if sort_by == "Cost" else "items"

df_topx = query(
    """
    SELECT
        vtm_id,
        vtm_name,
        pres_name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    from prescribing_agg AS rx
    INNER JOIN _selected_practices AS s
      ON rx.practice_code = s.practice_code
    GROUP BY GROUPING SETS (
    (vtm_name,vtm_id, pres_name),
    (vtm_name,vtm_id)
    )
""",
    dfs={
        "_selected_practices": pd.DataFrame({"practice_code": selected_practice_codes})
    },
)

df_topx_vtm = df_topx[df_topx["pres_name"].isna()]  # VTM-level rows
df_topx_detail = df_topx[df_topx["pres_name"].notna()]  # presentation-level rows

df_topx_ranked = (
    df_topx_vtm.groupby(["vtm_name", "vtm_id"])[["items", "actual_cost"]]
    .sum()
    .reset_index()
    .nlargest(top_n, sort_col)
)


for _, row in df_topx_ranked.iterrows():
    label = (
        f"{row['vtm_name']} — £{row['actual_cost']:,.2f} ({row['items']:,.0f} items)"
    )
    vtm_breakdown = df_topx_detail[df_topx_detail["vtm_id"] == row["vtm_id"]]

    with st.expander(label):
        st.dataframe(
            vtm_breakdown[["pres_name", "actual_cost", "items"]]
            .sort_values(sort_col, ascending=False)
            .assign(actual_cost=lambda d: d["actual_cost"].map("£{:,.2f}".format))
            .rename(
                columns={
                    "pres_name": "Presentation",
                    "actual_cost": "Cost",
                    "items": "Items",
                }
            ),
            hide_index=True,
        )
