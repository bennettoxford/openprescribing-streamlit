import altair as alt
import pandas as pd
import streamlit as st
from org_filter import org_filter_sidebar
from pathlib import Path
import yaml1

from db import create_materialised_view, query

st.set_page_config(layout="wide")

st.markdown(
    """
<style>
[data-testid="stDataFrame"] td { border: none !important; }
</style>
""",
    unsafe_allow_html=True,
)

create_materialised_view(name="prescribing_2025")

# App

# Header
st.image(Path("content/OpenPrescribing.svg"))
st.info(
"""##### Hello!  This is a **very** early prototype of displaying the top drugs used (by both items and cost) in 2025.  
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)

with st.expander("Click here to read our methodology", icon=":material/quick_reference:"):
    with open(Path("content/prescribing_topx/methodology.md")) as f:
        st.markdown(f.read())
        

# --- Sidebar filters ---

selected_practice_codes = org_filter_sidebar()

with st.sidebar:

    top_n = st.slider("Top N items", min_value=5, max_value=100, value=20)
    sort_by = st.radio("Sort by", ["Cost", "Items"], horizontal=True)

sort_col = "actual_cost" if sort_by == "Cost" else "items"

df_topx = query(
    f"""
    SELECT
        vtm_id,
        vtm_name,
        pres_name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    FROM prescribing_2025 AS rx
    WHERE practice_code IN {selected_practice_codes} 
    GROUP BY GROUPING SETS (
    (vtm_name,vtm_id, pres_name),
    (vtm_name,vtm_id)
    )
    """
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

st.divider()

with open(Path("content/prescribing_topx/changelog.yaml")) as f:
    changelog = yaml.safe_load(f)

with st.expander("Click to see changelog", icon=":material/history:"):
    for entry in reversed(changelog):
        st.markdown(f"**{entry['date']}** — {entry['change']} *({entry['person']})*")