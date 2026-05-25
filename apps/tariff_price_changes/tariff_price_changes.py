import streamlit as st
from pathlib import Path
import pandas as pd
import yaml

from db import create_materialised_view, query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = "tariff_price_changes" # defines the tool name

# --- Functions ---

# creates filtered prescribing table, based on selected date - puts into cache so only run if selected date changes
@st.cache_data
def get_date_filtered(tool_name, prescribing_date, selected_date):
    return query(
        f"""
        SELECT
            rx.snomed_code,
            rx.practice_code,
            med.name,
            dt.tariff_cat,
            rx.quantity * dt.price_diff_pu * dt.is_max_price_diff_pu AS price_difference
        FROM {tool_name}_prescribing AS rx
        INNER JOIN {tool_name}_price_changes AS dt 
            ON rx.snomed_code = dt.vpid
            AND dt.date = '{selected_date}'
        INNER JOIN medications AS med ON rx.snomed_code = med.id
        WHERE rx.date = '{prescribing_date}'
        """
    )

# render a per-category increase/decrease/unchanged summary
def render_summary(df):

    summary = (
        df.groupby(["tariff_category", "price_change"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for _, row in summary.iterrows():
        st.markdown(f"**Category: {row['tariff_category']}**")
        c1, c2, c3 = st.columns(3)
        c1.write(f"Increases: {row.get('increase', 0)}")
        c2.write(f"Decreases: {row.get('decrease', 0)}")
        c3.write(f"No change: {row.get('unchanged', 0)}")

# render paginated expanders for each BNF presentation
def render_tariff_row(row):
    colour = "red" if row["price_difference"] > 0 else "green"
    label = f":{colour}[{row['name']}: {gbp(row['price_difference'], 2)}]"
    vmpp_details = vmpp_df[(vmpp_df["vpid"] == row["snomed_code"]) & (vmpp_df["date"] == selected_date)].copy()
    with st.expander(label):
        display_df = vmpp_details[["nm", "price_pence", "previous_price_pence", "tariff_category"]].copy()
        display_df["price_pence"] = (pd.to_numeric(display_df["price_pence"], errors="coerce") / 100).apply(lambda x: gbp(x, dp=2))
        display_df["previous_price_pence"] = (pd.to_numeric(display_df["previous_price_pence"], errors="coerce") / 100).apply(lambda x: gbp(x, dp=2))
        display_df = display_df.rename(columns={
            "nm": "Name",
            "price_pence": "Price",
            "previous_price_pence": "Previous Price",
            "tariff_category": "DT Category"
        })
        st.dataframe(display_df, hide_index=True, use_container_width=True)


# --- Initialisation ---

create_materialised_view(name="price_changes", tool_name=tool_name, app_file=__file__) # creates the price changes table
create_materialised_view(name="vmpp", tool_name=tool_name, app_file=__file__) # creates the vmpp table
create_materialised_view(name="prescribing", tool_name=tool_name, app_file=__file__) # creates the prescribing table


# --- Data ---


vmpp_df = query(f"SELECT * FROM {tool_name}_vmpp") # creates vmpp_df from materialised view

# creates distinct tariff categories to use with sidebar category filter
tariff_cat_df = ( 
    query(f"SELECT DISTINCT tariff_cat FROM {tool_name}_price_changes ORDER BY tariff_cat")["tariff_cat"]
    .dropna()
    .tolist()
)

# creates distinct dates to use with sidebar date filter
dates = query(f"""
    SELECT DISTINCT date FROM {tool_name}_price_changes
    ORDER BY date DESC
""")["date"].tolist()

max_rx_date = query("SELECT MAX(date) FROM date")["max(date)"][0] # returns latest date available in prescribing data


# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of estimating the impact of drug tariff changes.
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)

# Drug Tariff explainer
with st.expander(
    "Click here to learn more about different Drug Tariff categories", icon=":material/question_mark:"
):
    with open(Path(__file__).parent / "content/questions.md") as f:
        st.markdown(f.read())

# Methodology explainer
with st.expander(
    "Click here to read our methodology", icon=":material/quick_reference:"
):
    with open(Path(__file__).parent / "content/methodology.md") as f:
        st.markdown(f.read())

# Sidebar 

# header
with st.sidebar:
    st.markdown("## **Drug Tariff changes estimator**")

# date selector   
with st.sidebar:
    st.header("Filters")
    selected_date = st.selectbox(
        "Select month",
        options=dates,
        format_func=lambda d: d.strftime("%B %Y")
    )

# creates either selected date, or maximum prescribing date if actual prescribing date not available
prescribing_date = selected_date if selected_date <= max_rx_date else max_rx_date

# returns month used for estimate
with st.sidebar:
    st.info(f"**Prescribing data used for estimate:** {prescribing_date.strftime('%B %Y')}")

# shows cascading organisation filter
selected_practice_codes, _ = org_filter_sidebar()

with st.sidebar:

    # Drug Tariff category filter
    with st.expander("Tariff Filter", expanded=False, icon=":material/book_ribbon:"):
        sel_tariff_cat = st.multiselect(
            "DT Category",
            sorted(tariff_cat_df),
            key="sel_tariff_cat",
        )

    # sort by radio buttons    
    with st.expander("Sort Options", expanded=False, icon=":material/sort:"):
        sort_option = st.radio(
            "Sort by",
            ["Largest Increases", "Largest Reductions"],
            key="sort_option",
        )

# gives navigation to other tools
sidebar_nav()


# Main app


date_filtered_df = get_date_filtered(tool_name, prescribing_date, selected_date) # filters data

# filters by selected practices, otherwise returns all practices (i.e. national)
if selected_practice_codes:
    date_filtered_df = date_filtered_df[date_filtered_df["practice_code"].isin(selected_practice_codes)]

# calculates aggregated data 
filtered_df = (
    date_filtered_df
    .groupby(["snomed_code", "name", "tariff_cat"])
    .agg(price_difference=("price_difference", "sum"))
    .reset_index()
)

# filters by tariff category if selected
if sel_tariff_cat:
    filtered_df = filtered_df[filtered_df["tariff_cat"].isin(sel_tariff_cat)]

# Show results
total_difference = filtered_df["price_difference"].sum() # calculates total difference

# displays total difference (formatted to 0 df)
st.info(
    f"#### Total estimated monthly price difference for {selected_date.strftime('%B %Y')}: {gbp(total_difference, 0)}"
    )

# displays breakdown
st.markdown("#### Breakdown by presentation")
st.info("ℹ️ To see details on changes to individual packs, click on the arrow")
st.markdown(
    """
    <style>
    details { border: none !important; box-shadow: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# apply sorting
sorted_df = filtered_df.sort_values(
    "price_difference", ascending=(sort_option != "Largest Increases")
)

# display breakdown
render_pagination(sorted_df, render_tariff_row)

# show summary
with st.expander(f"See total number of national Drug Tariff changes for {selected_date.strftime('%B %Y')}"):
    render_summary(vmpp_df)


# show changelog
changelog(Path(__file__).parent)