import time
from pathlib import Path

import streamlit as st

from db import query
from utils import (
    changelog,
    global_styles,
    org_filter_sidebar,
    sidebar_logo,
    sidebar_nav,
)

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---
tool_name = Path(__file__).parent.name
app_path = Path(__file__).parent

# --- Functions ---


# gets dates for the data selector
@st.cache_data
def get_dates():
    return query(
        f"SELECT DISTINCT date FROM {tool_name}_gbg_prescribing ORDER BY date ASC"
    )["date"].tolist()


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
with (
    st.expander(
        "Click here to read our methodology", icon=":material/quick_reference:"
    ),
    open(Path(__file__).parent / "content/methodology.md") as f,
):
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
with (
    st.sidebar,
    st.expander(
        "Change time period for breakdown",
        icon=":material/calendar_month:",
        expanded=False,
    ),
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


medications_query = """
    SELECT DISTINCT
        id
    FROM medications
    WHERE SUBSTR(bnf_code, 10, 2) = 'AA'
    AND id != vmp_id
    AND vmp_id IN (
        SELECT DISTINCT vmp_id
        FROM medications
        INNER JOIN vmpp
            ON vmpp.vpid = medications.vmp_id
        INNER JOIN data_tariffprice
            ON data_tariffprice.vmpp_id = vmpp.vppid
        WHERE data_tariffprice.date>= '2024-04-01'
    )
    AND id IN (
        SELECT DISTINCT snomed_code
        FROM prescribing
    )
"""

start = time.perf_counter()
medications_df = query(medications_query)
elapsed = time.perf_counter() - start

with st.expander("Query info"):
    st.write(f"Rows returned: {len(medications_df)}")
    st.write(f"Time: {elapsed:.3f}s")

st.dataframe(medications_df)

# show changelog
changelog(Path(__file__).parent)

medications_df = query(medications_query)
snomed_codes = medications_df["id"].to_list()
prescribing_query = """
SELECT *
FROM prescribing
WHERE snomed_code IN (    SELECT DISTINCT
        id
    FROM medications
    WHERE SUBSTR(bnf_code, 10, 2) = 'AA'
    AND id != vmp_id
    AND vmp_id IN (
        SELECT DISTINCT vmp_id
        FROM medications
        INNER JOIN vmpp
            ON vmpp.vpid = medications.vmp_id
        INNER JOIN data_tariffprice
            ON data_tariffprice.vmpp_id = vmpp.vppid
        WHERE data_tariffprice.date>= '2024-04-01'
    )
    AND id IN (
        SELECT DISTINCT snomed_code
        FROM prescribing
    ))
"""

start = time.perf_counter()
prescribing_df = query(prescribing_query)
elapsed = time.perf_counter() - start

with st.expander("Query info"):
    st.write(f"Rows returned: {len(prescribing_df)}")
    st.write(f"Time: {elapsed:.3f}s")

st.dataframe(prescribing_df)

prescribingnm_query = f"""
SELECT *
FROM prescribing
INNER JOIN medications
ON
medications.id = prescribing.snomed_code
WHERE snomed_code IN ({", ".join(f"'{c}'" for c in snomed_codes)})
AND practice_code = 'L83081'
"""

start = time.perf_counter()
# prescribingnm_df = query(prescribingnm_query)
elapsed = time.perf_counter() - start

with st.expander("Query info"):
    st.write(f"Rows returned: {len(prescribingnm_df)}")
    st.write(f"Time: {elapsed:.3f}s")

st.dataframe(prescribing_df)
