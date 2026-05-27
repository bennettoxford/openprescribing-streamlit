import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt

from db import create_materialised_view, query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df, combine_threshold_slider, combine_small_categories
from charts import plot_decile_chart, plot_stacked_area,     breakdown_chart_type_selector,     plot_breakdown_chart

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
##### Hello!  This is a **very** early prototype of new visualisations for our measure on AWaRe antibiotics.
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
    st.markdown("### Antibiotic stewardship: Access, Watch and Reserve (AWaRe) antibiotics")


# shows cascading organisation filter
selected_practice_codes, sql_in, level = org_filter_sidebar()

combine_threshold = combine_threshold_slider()

# gives navigation to other tools
sidebar_nav()


# Main app

# Main meaure decile chart

# calculate decile charts
measure_df  = load_proportion_rates(
    table_name="measure_aware_aware_prescribing", # materialised view for the data
    value_col="items", # measure calculation type
    numerator_condition="aware_2024 IN ('Watch', 'Reserve')" ,
    denominator_condition="aware_2024 IN ('Access', 'Watch', 'Reserve')"
)

deciles_df = load_deciles(measure_df)
practice_df = load_practice_df() # get data from cascade filter

decile_level = "icb" if level == "national" else level #sets the level of deciles being shown - if nothing selected, shows ICB level deciles
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level] # filters the deciles to the correct level filtered in the cascade 
measure_filtered = filter_rates(measure_df, level, selected_practice_codes, practice_df) # filters the measure to the correct level

chart_title = "Percentage of antibiotic prescriptions that are for Watch and Reserve group antibiotics" # create chart title
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=chart_title) # plots decile charts


# creates aware_df from materialised view
stacked_df = query(
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
    ORDER BY items DESC
    """
) 

#st.dataframe(aware_df)

with st.expander(
    "Click here to see a stacked time chart of AWaRe categories", icon=":material/stacked_line_chart:"
):
    plot_stacked_area(
        stacked_df,
        x_col="date",
        y_col="items",
        color_col="aware_2024",
        sort_order="descending"
    )

aware_details_df = query(
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


aware_details_breakdown_df = query(
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
    ORDER BY items DESC
    """
) # creates aware_df from materialised view

with st.expander(
    "Click here to see a breakdown of drugs in the numerator", icon=":material/donut_large:"
):
    st.info("Click on drug in bar or donut chart to see breakdown by presentation")

    chart_type = breakdown_chart_type_selector()

    combined_df = combine_small_categories(
        aware_details_df,
        category_col="vtm_name",
        value_col="items",
        threshold=combine_threshold,
    )

    selected_category = plot_breakdown_chart(
        combined_df,
        value_col="items",
        category_col="vtm_name",
        chart_type=chart_type,
        key="aware_breakdown_chart",
    )

    if selected_category:

        filtered_df = (
            aware_details_breakdown_df[
                aware_details_breakdown_df["vtm_name"] == selected_category
            ]
            .drop(columns="vtm_name")
            .sort_values("items", ascending=False)
        )

        st.markdown(f"##### Products containing {selected_category} prescribed in the last three months")

        st.dataframe(
            filtered_df,
            hide_index=True,
            width="stretch",
            column_config={
                "name": "Medicine",
                "items": st.column_config.NumberColumn(
                    "Items",
                    format="%,d",
                ),
            },
        )

# show changelog
changelog(Path(__file__).parent)