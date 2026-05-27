import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path
import yaml

from utils import sidebar_logo, sidebar_nav, org_filter_sidebar, gbp, global_styles, changelog
from db import create_materialised_view, query

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = "prescribing_topx" # defines the tool name

app_path = Path(__file__).parent # defines the path for content

# --- Functions ---

# --- Initialisation ---

create_materialised_view(name="prescribing_2025", tool_name=tool_name, app_file=__file__) # creates the price changes table

# --- Data ---

# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# Header
st.info(
"""
##### Hello!  This is a **very** early prototype of displaying the top drugs used (by both items and cost) in 2025.  
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)

st.markdown(
    """
<style>
[data-testid="stDataFrame"] td { border: none !important; }
</style>
""",
    unsafe_allow_html=True,
)

# Methodology explainer
with st.expander(
    "Click here to read our methodology", icon=":material/quick_reference:"
):
    with open(Path(__file__).parent / "content/methodology.md") as f:
        st.markdown(f.read())
        
# Sidebar 

# header
with st.sidebar:
    st.markdown("## **Top prescribing by items and cost**")


# shows cascading organisation filter
selected_practice_codes, _, _ = org_filter_sidebar()

with st.sidebar:

    # Select number of items
        with st.expander("Number of drugs to show", expanded=False, icon=":material/tune:"):
            top_n = st.slider(
                "Top N items", 
                min_value=5, 
                max_value=100, 
                value=20
            )

    # sort by radio buttons
        with st.expander("Sort options", expanded=False, icon=":material/sort:"):
            sort_by = st.radio(
                "Sort by", 
                ["Cost", "Items"], 
                horizontal=True
            )


sort_col = "actual_cost" if sort_by == "Cost" else "items"

# gives navigation to other tools
sidebar_nav()


df_topx = query(
    f"""
    SELECT
        vtm_id,
        vtm_name,
        pres_name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    FROM {tool_name}_prescribing_2025 AS rx
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


# show changelog
changelog(app_path)