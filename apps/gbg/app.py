import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt

from db import query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df, combine_threshold_slider, combine_small_categories, load_per1000_rates, combine_small_categories_by_date
from charts import plot_decile_chart, plot_stacked_area,     breakdown_chart_type_selector,     plot_breakdown_chart

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---
tool_name = Path(__file__).parent.name
app_path = Path(__file__).parent

# --- Functions ---

# gets dates for the data selector
@st.cache_data
def get_dates():
    return query(f"SELECT DISTINCT date FROM {tool_name}_gbg_prescribing ORDER BY date ASC")["date"].tolist()


# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of Ghost Branded Generics viewer.
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
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
    st.markdown("### Ghost Branded Generics")


# shows cascading organisation filter
selected_practice_codes, sql_in, level = org_filter_sidebar()

# get dates
dates_asc = get_dates()

# creates date slider, defaulting to latest 3 months
with st.sidebar:
    with st.expander(
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

gbg_details_df = query(
    f"""
    SELECT
        snomed_code as dmd_code,
        medications.name as name,
        SUM(items) AS total_items
    FROM {tool_name}_gbg_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    GROUP BY 
        dmd_code,
        name
    ORDER BY 
        total_items DESC
    """
) # creates gbg breakdown


st.dataframe(gbg_details_df)

# show changelog
changelog(Path(__file__).parent)