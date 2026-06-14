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
    return query(f"SELECT DISTINCT date FROM {tool_name}_ome_prescribing ORDER BY date ASC")["date"].tolist()


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
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=chart_title, y_format=".0f", y_title="OME per 1000 patients (mg)") # plots decile charts



with st.expander(
    "Click here to see a stacked time chart of opioids",
    icon=":material/stacked_line_chart:",
):

    mode = st.radio(
        "Group by",
        ["ing", "vtm"],
        format_func=lambda x: {"ing": "Ingredient", "vtm": "Chemical Substance"}[x],
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
        y_title="Total OME (mg)"
    )

with st.expander(
    f"Click here to see a breakdown of drugs prescribed between {start_date.strftime('%b %Y')} and {end_date.strftime('%b %Y')}", icon=":material/donut_large:"
):
    st.info("""
        Click on drug in bar or donut chart to see breakdown by presentation.

        You can change the date range by using the slide in the sidebar.
        """
    )

    mode_breakdown = st.radio(
        "Group by",
        ["ing", "vtm"],
        format_func=lambda x: {"ing": "Ingredient", "vtm": "Chemical Substance"}[x],
        horizontal=True,
        key="stacked_chart_groupby_breakdown",
    )

    groupings = {
        "ing": {
            "cols": "ingredient_id, ing_name",
            "group_by": "rx.ingredient_id, rx.ing_name",
            "color_col": "ing_name",
            "id_col": "ingredient_id",
            "y_title": "Ingredient Name",
        },
        "vtm": {
            "cols": "vtm_id, vtm_name",
            "group_by": "rx.vtm_id, rx.vtm_name",
            "color_col": "vtm_name",
            "id_col": "vtm_id",
            "y_title": "Chemical Substance",
        },
    }

    group_cols_breakdown = groupings[mode_breakdown]["cols"]
    color_col_breakdown = groupings[mode_breakdown]["color_col"]
    group_by_breakdown = groupings[mode_breakdown]["group_by"]
    id_col_breakdown = groupings[mode_breakdown]["id_col"]

    details_df = query(
    f"""
    SELECT
        {group_by_breakdown},
        SUM(total_ome) AS total_ome
    FROM {tool_name}_ome_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    GROUP BY {group_by_breakdown}
    """
)

    details_breakdown_df = query(
        f"""
        SELECT
            rx.name AS name,
            {group_by_breakdown},
            SUM(items) AS items,
            SUM(quantity) AS quantity,
            SUM(total_ome) AS total_ome
        FROM {tool_name}_ome_prescribing AS rx
        INNER JOIN medications
        ON rx.snomed_code = medications.id
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND rx.practice_code IN {sql_in}
        GROUP BY
            {group_by_breakdown},
            rx.name
        ORDER BY total_ome DESC
        """
    )

    chart_type = breakdown_chart_type_selector()

    combined_df = combine_small_categories(
        details_df,
        category_col=color_col_breakdown,
        value_col="total_ome",
        threshold=combine_threshold,
    )

    selected_category = plot_breakdown_chart(
        combined_df,
        value_col="total_ome",
        category_col=color_col_breakdown,
        chart_type=chart_type,
        key=f"aware_breakdown_chart_{mode_breakdown}",
        y_title=groupings[mode_breakdown]["y_title"],
        x_title="Total OME (mg)"
    )

    if selected_category:

        if selected_category == "Other":
            kept_categories = set(
                combined_df.loc[combined_df[color_col_breakdown] != "Other", color_col_breakdown]
            )

            filtered_df = (
                details_breakdown_df[
                    ~details_breakdown_df[color_col_breakdown].isin(kept_categories)
                ]
                .drop(columns=color_col_breakdown)
                .sort_values("total_ome", ascending=False)
            )
        else:
            filtered_df = (
                details_breakdown_df[
                    details_breakdown_df[color_col_breakdown] == selected_category
                ]
                .drop(columns=[color_col_breakdown, id_col_breakdown])
                .sort_values("total_ome", ascending=False)
            )

        st.markdown(f"##### Products containing {selected_category} prescribed between {start_date.strftime('%b %Y')} and {end_date.strftime('%b %Y')}")

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
                "quantity": st.column_config.NumberColumn(
                    "Quantity",
                    format="%,d",
                ),
                "total_ome": st.column_config.NumberColumn(
                    "Total OME",
                    format="%,.1f",
                ),
            },
        )

# show changelog
changelog(Path(__file__).parent)