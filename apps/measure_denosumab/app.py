from pathlib import Path

import streamlit as st

from charts import (
    plot_decile_chart,
)
from db import query
from utils import (
    filter_rates,
    global_styles,
    load_deciles,
    load_per1000_rates,
    load_practice_df,
    org_filter_sidebar,
    sidebar_logo,
    sidebar_nav,
    why_it_matters,
)

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = Path(__file__).parent.name # defines the tool name
app_path = Path(__file__).parent

# --- Functions ---

# gets dates for the data selector
@st.cache_data
def get_dates():
    return query(f"SELECT DISTINCT date FROM {tool_name}_measure_denosumab ORDER BY date ASC")["date"].tolist()


# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of new visualisations for our measure on Hypnotic and Anxiolytic Average Daily Quantities (ADQs).
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)

# Methodology explainer
with st.expander(
    "Click here to read our methodology", icon=":material/quick_reference:"
), open(Path(__file__).parent / "content/methodology.md") as f:
    st.markdown(f.read())

# show why_it_matters
why_it_matters(app_path)

# Sidebar 

# header
with st.sidebar:
    st.markdown("### Use of biosimilar denosumab 60mg")


# shows cascading organisation filter
selected_practice_codes, sql_in, level = org_filter_sidebar()

# get dates
dates_asc = get_dates()

# creates date slider, defaulting to latest 3 months
with st.sidebar, st.expander(
    "Change time period for breakdown", icon=":material/calendar_month:", expanded=False
    ):
        start_date, end_date = st.select_slider(
            "Date range",
            options=dates_asc,
            value=(dates_asc[-3], dates_asc[-1]),  # defaults to latest 3 months
            format_func=lambda d: d.strftime("%b %Y"),
        )

# gives navigation to other tools
sidebar_nav()


# Main app

# Main meaure decile chart

# calculate decile charts
measure_df = load_per1000_rates(
    table_name=f"{tool_name}_measure_denosumab",
    value_col="actual_cost",
    denom_table="list_size",
    denom_col="total"
)

deciles_df = load_deciles(measure_df)
practice_df = load_practice_df() # get data from cascade filter

decile_level = "icb" if level == "national" else level #sets the level of deciles being shown - if nothing selected, shows ICB level deciles
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level] # filters the deciles to the correct level filtered in the cascade 
measure_filtered = filter_rates(measure_df, level, selected_practice_codes, practice_df) # filters the measure to the correct level

chart_title = "Denosumab cost (£) per 1000 patients" # create chart title
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=chart_title, y_format=".1f", y_title="OME per 1000 patients (mg)") # plots decile charts

with st.expander("Click to see something"):
    mode = st.radio(
        "Group by",
        ["costper1000", "costperunit"],
        format_func=lambda x: {"costper1000": "Cost per 1000 patients", "costperunit": "Cost per unit"}[x],
        horizontal=True,
        key="stacked_chart_groupby",
    )

mode_config = {
    "costper1000": {
        "value_col": "actual_cost",
        "denom_table": "list_size",
        "denom_col": "total",
        "scale": 1000.0,
        "chart_title": "Denosumab cost (£) per 1000 patients",
        "y_format": ".1f",
        "y_title": "Cost per 1000 patients (£)",
    },
    "costperunit": {
        "value_col": "actual_cost",
        "denom_table": None,
        "denom_col": "quantity",
        "scale": 1.0,
        "chart_title": "Denosumab cost (£) per unit",
        "y_format": ".2f",
        "y_title": "Cost per unit (£)",
    },
}

cfg = mode_config[mode]

measure_df = load_per1000_rates(
    table_name=f"{tool_name}_measure_denosumab",
    value_col=cfg["value_col"],
    denom_table=cfg["denom_table"],
    denom_col=cfg["denom_col"],
    scale=cfg.get("scale", 1000.0),
)

deciles_df = load_deciles(measure_df)
practice_df = load_practice_df()
decile_level = "icb" if level == "national" else level
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level]
measure_filtered = filter_rates(measure_df, level, selected_practice_codes, practice_df)
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=cfg["chart_title"], y_format=cfg["y_format"], y_title=cfg["y_title"], key=f"decile_chart_{mode}")