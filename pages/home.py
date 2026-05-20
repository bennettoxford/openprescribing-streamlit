import streamlit as st
from pathlib import Path

st.set_page_config(layout="wide")

st.image(Path("content/OpenPrescribing.svg"))
st.info(
"""#### Hello!  You've found our streamlit prototyping page
##### This is where we're testing new tools that we think may be useful.
This is our 'sandbox', and so things you find on here may not be accurate, and may break or change from time to time.  
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)