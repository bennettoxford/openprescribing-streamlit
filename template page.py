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




# --- Initialisation ---




# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of estimating the impact of .
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
    st.markdown("## ****")


# shows cascading organisation filter
selected_practice_codes, _ = org_filter_sidebar()


# gives navigation to other tools
sidebar_nav()


# Main app


date_filtered_df = get_date_filtered(tool_name, prescribing_date, selected_date) # filters data



# show changelog
changelog(Path(__file__).parent)