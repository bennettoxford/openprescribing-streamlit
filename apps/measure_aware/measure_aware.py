import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt

from db import create_materialised_view, query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df
from charts import plot_decile_chart

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = "measure_aware" # defines the tool name
app_path = Path(__file__).parent

# --- Functions ---




# --- Initialisation ---


create_materialised_view(name="aware_prescribing", tool_name=tool_name, app_file=__file__) # creates the aware table

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

# show why_it_matters
why_it_matters(app_path)

# Sidebar 

# header
with st.sidebar:
    st.markdown("## ****")


# shows cascading organisation filter
selected_practice_codes, sql_in, level = org_filter_sidebar()


# gives navigation to other tools
sidebar_nav()


# Main app


rates_df    = load_proportion_rates(
    table_name="measure_aware_aware_prescribing",
    value_col="items",
    numerator_condition="aware_2024 = 'Access'"
)

deciles_df = load_deciles(rates_df)
practice_df = load_practice_df()

decile_level = "practice" if level == "national" else level
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level]
rates_filtered = filter_rates(rates_df, level, selected_practice_codes, practice_df)


plot_decile_chart(deciles_filtered, level, rates_filtered)






aware_df = query(
    f"""
    SELECT
        date, 
        aware_2024, 
        SUM(items) AS items 
    FROM {tool_name}_aware_prescribing as rx
    WHERE rx.practice_code IN {sql_in}
    GROUP BY 
        date,
        aware_2024
    """
) # creates aware_df from materialised view

#st.dataframe(aware_df)

chart = (
    alt.Chart(aware_df)   
    .mark_area()           
    .encode(
        x='date:T',          # x axis is date, :T means temporal (date/time) type
        y=alt.Y('items:Q', stack=True),  # y axis is sum of items, :Q means quantitative (numeric) type
        color='aware_2024:N' # one colour per aware category, :N means nominal (categorical) type
    )
)

st.altair_chart(chart, use_container_width=True)

aware_donut_df = query(
    f"""
    SELECT
        vtm.nm AS vtm_name,
        SUM(items) AS items 
    FROM {tool_name}_aware_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    INNER JOIN vtm
    ON
    medications.vtm_id = vtm.vtmid
    WHERE date >= (SELECT MAX(date) - INTERVAL '3 months' FROM date)
    AND rx.practice_code IN {sql_in}
    AND aware_2024 = 'Watch'
    GROUP BY 
        vtm.nm 
    """
) # creates aware_df from materialised view

total = aware_donut_df ['items'].sum()
aware_donut_df ['vtm_name'] = aware_donut_df .apply(
    lambda row: row['vtm_name'] if row['items'] / total >= 0.02 else 'Other',
    axis=1
)
aware_donut_df  = aware_donut_df .groupby('vtm_name', as_index=False)['items'].sum()

aware_donut_details_df = query(
    f"""
    SELECT
        rx.name AS name,
        vtm.nm AS vtm_name,
        SUM(items) AS items 
    FROM {tool_name}_aware_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    INNER JOIN vtm
    ON
    medications.vtm_id = vtm.vtmid
    WHERE date >= (SELECT MAX(date) - INTERVAL '3 months' FROM date)
    AND rx.practice_code IN {sql_in}
    AND aware_2024 = 'Watch'
    GROUP BY 
        vtm.nm,
        rx.name
    """
) # creates aware_df from materialised view

total = aware_donut_details_df ['items'].sum()
aware_donut_details_df ['vtm_name'] = aware_donut_details_df .apply(
    lambda row: row['vtm_name'] if row['items'] / total >= 0.02 else 'Other',
    axis=1
)
aware_donut_details_df  = aware_donut_details_df .groupby(['vtm_name', 'name'], as_index=False)['items'].sum()

def render_chart(data_df, details_df, value_col, category_col, chart_type="donut"):
    selection_param = alt.selection_point(name='my_selection', fields=[category_col])

    if chart_type == "donut":
        chart = (
            alt.Chart(data_df)
            .mark_arc(innerRadius=50)
            .encode(
                theta=f'{value_col}:Q',
                color=f'{category_col}:N'
            )
            .add_params(selection_param)
        )
    else:
        chart = (
            alt.Chart(data_df)
            .mark_bar()
            .encode(
                x=f'{value_col}:Q',
                y=f'{category_col}:N',
                color=f'{category_col}:N'
            )
            .add_params(selection_param)
        )

    chart_selection = st.altair_chart(chart, on_select="rerun", use_container_width=True)

    if chart_selection.selection.my_selection:
        selected_category = chart_selection.selection.my_selection[0][category_col]
        st.dataframe(details_df[details_df[category_col] == selected_category])


st.radio("Chart type", ["donut", "bar"], horizontal=True, key="chart_type")

render_chart(aware_donut_df, aware_donut_details_df, 'items', 'vtm_name', st.session_state.chart_type)


test_org_df = query(
    f"""
    WITH orgs AS (
        SELECT
            prac.id AS practice_code,
            MAX(CASE WHEN par.org_type = 'pcn' THEN par.id END) AS pcn_code,
            MAX(CASE WHEN par.org_type = 'icb' THEN par.id END) AS icb_code,
            MAX(CASE WHEN par.org_type = 'reg' THEN par.id END) AS region_code
        FROM org AS prac
        INNER JOIN org_relation AS rel ON prac.id = rel.child_id
        INNER JOIN org AS par ON rel.parent_id = par.id
        WHERE prac.org_type = 'pra'
        AND prac.inactive = 0
        GROUP BY prac.id
    ),
    base AS (
        SELECT
            date,
            o.practice_code,
            o.pcn_code,
            o.icb_code,
            o.region_code,
            CASE 
                WHEN o.practice_code IS NOT NULL THEN 'practice'
                WHEN o.pcn_code      IS NOT NULL THEN 'pcn'
                WHEN o.icb_code      IS NOT NULL THEN 'icb'
                WHEN o.region_code   IS NOT NULL THEN 'region'
            END AS org_type,
            SUM(CASE WHEN aware_2024 = 'Access' THEN items ELSE 0 END) AS numerator,
            SUM(items) AS denominator,
            numerator / NULLIF(denominator, 0) AS rate
        FROM {tool_name}_aware_prescribing AS rx
        JOIN orgs AS o ON rx.practice_code = o.practice_code
        GROUP BY GROUPING SETS (
            (date, o.practice_code),
            (date, o.pcn_code),
            (date, o.icb_code),
            (date, o.region_code)
        )
    )
    SELECT
        *,
        NTILE(10) OVER (
            PARTITION BY org_type, date
            ORDER BY rate
        ) AS decile
    FROM base
    """
)

# show changelog
changelog(Path(__file__).parent)