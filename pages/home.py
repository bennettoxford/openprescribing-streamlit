import streamlit as st

from utils import global_styles, sidebar_logo, sidebar_nav

st.set_page_config(layout="wide")

# --- App ---

# inserts logo into sidebar
sidebar_logo()

with st.sidebar:
    st.info(
        """ℹ️ The majority of these tools allow you to select multiple organisations at different levels in the NHS, including

- NHS Region
- Integrated Care Board (ICB)
- Sub-ICB level (former CCGs)
- Primary Care Networks (PCNs)
- GP Practices
"""
    )

# applies CSS for navigation bar
global_styles()

# gives navigation to other tools
sidebar_nav()

st.info(
    """#### Hello!  You've found OpenPrescribing Workbench.

##### This is our prototyping page, where we're trying out new tools using [Streamlit](https://streamlit.io/), an open-source Python framework for building data visualisations, which allows us to test things quickly and see if they're useful.

As this is our 'sandbox' things you find on here may not be accurate, and may break, change, or disappear from time to time.  You can see how we are building things by clicking on the "read our methodology" in each tool, and keep track of changes by
clicking on the changelog.

Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)

st.markdown("#### Prototype tools available")


st.markdown("##### Cost tools")
st.page_link(
    "apps/tariff_price_changes/app.py",
    label="Drug Tariff changes",
    icon=":material/book_5:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See what the estimated financial impact of Drug Tariff changes have been every month since April 2024</p>',
    unsafe_allow_html=True,
)

st.page_link(
    "apps/prescribing_topx/app.py",
    label="Top prescriptions by items and cost",
    icon=":material/table_chart_view:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See what the highest number of prescriptions were in 2025, in terms of both cost and prescription items</p>',
    unsafe_allow_html=True,
)

st.markdown("##### Prescribing measures")
st.page_link(
    "apps/measure_aware/app.py",
    label="Access, Watch, Reserve (AWaRe) antibiotic prescribing",
    icon=":material/coronavirus:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See the proportion of antibiotics prescribed by each AWaRe category, including different visualisations and breakdowns</p>',
    unsafe_allow_html=True,
)

st.page_link(
    "apps/measure_hypnotics/app.py",
    label="Hypnotic and anxiolytic Average Daily Quantity (ADQ) prescribing",
    icon=":material/moon_stars:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See the level of prescribing of anxiolytics and hypnotics, including different visualisations and breakdowns</p>',
    unsafe_allow_html=True,
)

st.page_link(
    "apps/measure_ome/app.py",
    label="Opioid Oral Morphine Equivalence (OME) prescribing",
    icon=":material/pill:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See the level of prescribing of all opioids by their equivalency to morphine, including different visualisations, breakdowns and selecting by ingredient or chemical substance</p>',
    unsafe_allow_html=True,
)

st.markdown("##### Quality improvement tools")
st.page_link(
    "apps/improvement_radar/app.py",
    label="Sub-ICB Level Improvement Radar",
    icon=":material/radar:",
)
st.markdown(
    '<p style="margin-left: 2.2rem; margin-top: -0.8rem; font-size: 0.875rem;">See whether other Sub-ICB level organisations have made improvements on their prescribing, to encourage sharing of ideas</p>',
    unsafe_allow_html=True,
)
