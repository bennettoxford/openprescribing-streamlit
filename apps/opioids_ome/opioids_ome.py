import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt

from db import create_materialised_view, query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df, combine_threshold_slider, combine_small_categories, load_per1000_rates, combine_small_categories_by_date
from charts import plot_decile_chart, plot_stacked_area,     breakdown_chart_type_selector,     plot_breakdown_chart

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = "opioids_ome" # defines the tool name
app_path = Path(__file__).parent

# --- Functions ---




# --- Initialisation ---


create_materialised_view(name="ome_prescribing", tool_name=tool_name, app_file=__file__) # creates the OME table

# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of new visualisations for our measure on Oral Morphine Equivalance per 1000 patients.
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
    st.markdown("### Total opioid prescribing (as oral morphine equivalence) per 1000 patients")


# shows cascading organisation filter
selected_practice_codes, sql_in, level = org_filter_sidebar()

combine_threshold = combine_threshold_slider()

# gives navigation to other tools
sidebar_nav()


# Main app

# Main meaure decile chart

# calculate decile charts
measure_df = load_per1000_rates(
    table_name=f"{tool_name}_ome_prescribing",
    value_col="total_ome",
    denom_table="list_size",
    denom_col="total"
)

deciles_df = load_deciles(measure_df)
practice_df = load_practice_df() # get data from cascade filter

decile_level = "icb" if level == "national" else level #sets the level of deciles being shown - if nothing selected, shows ICB level deciles
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level] # filters the deciles to the correct level filtered in the cascade 
measure_filtered = filter_rates(measure_df, level, selected_practice_codes, practice_df) # filters the measure to the correct level

chart_title = "Oral Morphine Equivalence (mg) per 1000 patients" # create chart title
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=chart_title, y_format=".1f") # plots decile charts


# creates stacked_df from materialised view

with st.expander(
    "Click here to see a stacked time chart of opioids",
    icon=":material/stacked_line_chart:",
):

    mode = st.radio(
        "Group by",
        ["ing", "vtm"],
        horizontal=True,
        key="stacked_chart_groupby",
    )

    groupings = {
        "ing": {
            "cols": "ingredient_id, ing_name",
            "color_col": "ing_name",
        },
        "vtm": {
            "cols": "vtm_id, vtm_name",
            "color_col": "vtm_name",
        },
    }

    group_cols = groupings[mode]["cols"]
    color_col = groupings[mode]["color_col"]

    stacked_df = query(f"""
        SELECT
            date,
            {group_cols},
            SUM(total_ome) AS total_ome
        FROM {tool_name}_ome_prescribing AS rx
        WHERE rx.practice_code IN {sql_in}
        GROUP BY
            date,
            {group_cols}
        ORDER BY total_ome DESC
    """)

    stacked_df = combine_small_categories_by_date(
        stacked_df,
        date_col="date",
        category_col=color_col,
        value_col="total_ome",
        threshold=combine_threshold,
    )


    plot_stacked_area(
        stacked_df,
        x_col="date",
        y_col="total_ome",
        color_col=color_col,
    )

aware_details_df = query(
    f"""
    SELECT
        ing_name AS ing_name,
        SUM(total_ome) AS total_ome
    FROM {tool_name}_ome_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    WHERE date >= (SELECT MAX(date) - INTERVAL '3 months' FROM date)
    AND rx.practice_code IN {sql_in}
    GROUP BY 
        ing_name
    """
) # creates aware_df from materialised view


aware_details_breakdown_df = query(
    f"""
    SELECT
        rx.name AS name,
        ing_name AS ing_name,
        SUM(total_ome) AS total_ome
    FROM {tool_name}_ome_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    WHERE date >= (SELECT MAX(date) - INTERVAL '3 months' FROM date)
    AND rx.practice_code IN {sql_in}
    GROUP BY 
        ing_name,
        rx.name
    ORDER BY total_ome DESC
    """
) # creates aware_df from materialised view

with st.expander(
    "Click here to see a breakdown of drugs prescribed", icon=":material/donut_large:"
):
    st.info("Click on drug in bar or donut chart to see breakdown by presentation")

    chart_type = breakdown_chart_type_selector()

    combined_df = combine_small_categories(
        aware_details_df,
        category_col="ing_name",
        value_col="total_ome",
        threshold=combine_threshold,
    )

    selected_category = plot_breakdown_chart(
        combined_df,
        value_col="total_ome",
        category_col="ing_name",
        chart_type=chart_type,
        key="aware_breakdown_chart",
    )

    if selected_category:

        if selected_category == "Other":
            kept_categories = set(
                combined_df.loc[combined_df["ing_name"] != "Other", "ing_name"]
            )

            filtered_df = (
                aware_details_breakdown_df[
                    ~aware_details_breakdown_df["ing_name"].isin(kept_categories)
                ]
                .drop(columns="ing_name")
                .sort_values("total_ome", ascending=False)
            )
        else:
            filtered_df = (
                aware_details_breakdown_df[
                    aware_details_breakdown_df["ing_name"] == selected_category
                ]
                .drop(columns="ing_name")
                .sort_values("total_ome", ascending=False)
            )

        st.markdown(f"##### Products containing {selected_category} prescribed in the last three months")

        st.dataframe(
            filtered_df,
            hide_index=True,
            width="stretch",
            column_config={
                "name": "Medicine",
                "items": st.column_config.NumberColumn(
                    "total_ome",
                    format="%,d",
                ),
            },
        )

# show changelog
changelog(Path(__file__).parent)