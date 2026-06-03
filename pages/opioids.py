from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from db import query
from org_filter import org_filter_sidebar
from page_formatting import gbp

st.set_page_config(layout="wide")

# Get data source

# App

# Header
st.image(Path("content/OpenPrescribing.svg"))
st.info(
    """##### Hello!  This is a **very** early prototype of a themed measures page, focussing on opioid prescribing..
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)

#with st.expander(
 #   "Click here to read our methodology", icon=":material/quick_reference:"
#):
 #   with open(Path("content/tariff_price_changes/methodology.md")) as f:
 #       st.markdown(f.read())

# Sidebar filters

selected_practice_codes = org_filter_sidebar()