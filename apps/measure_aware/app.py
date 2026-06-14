import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt

from db import query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df, combine_threshold_slider, combine_small_categories
from charts import plot_decile_chart, plot_stacked_area,     breakdown_chart_type_selector,     plot_breakdown_chart

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = Path(__file__).parent.name # defines the tool name
app_path = Path(__file__).parent

# --- Functions ---

@st.cache_data
def get_dates():
    return query(f"SELECT DISTINCT date FROM {tool_name}_aware_prescribing ORDER BY date ASC")["date"].tolist()


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
measure_df  = load_proportion_rates(
    table_name=f"{tool_name}_aware_prescribing", # materialised view for the data
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
        sort_order="descending",
        y_title="Percentage of items as blah"
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
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    AND aware_2024 IN ('Watch','Reserve')
    GROUP BY 
        vtm.nm 
    """
)

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
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    AND aware_2024 IN ('Watch','Reserve')
    GROUP BY 
        vtm.nm,
        rx.name
    ORDER BY items DESC
    """
)

with st.expander(
    f"Click here to see a breakdown of drugs in the numerator between {start_date.strftime('%b %Y')} and {end_date.strftime('%b %Y')}", icon=":material/donut_large:"
):
    st.info("""
        Click on drug in bar or donut chart to see breakdown by presentation.

        You can change the date range by using the slider in the sidebar.
    """)

    include_watch, include_reserve, *_ = st.columns([1, 1, 8])
    include_watch = include_watch.checkbox("Watch", value=True)
    include_reserve = include_reserve.checkbox("Reserve", value=True)


    selected_aware = [c for c, selected in [("Watch", include_watch), ("Reserve", include_reserve)] if selected]
    if not selected_aware:
        st.warning("Please select at least one category.")
        st.stop()
    sql_aware = str(tuple(selected_aware)) if len(selected_aware) > 1 else f"('{selected_aware[0]}')"


    chart_type = breakdown_chart_type_selector()

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
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    AND aware_2024 IN {sql_aware}
    GROUP BY 
        vtm.nm 
    """
)

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
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    AND aware_2024 IN {sql_aware}
    GROUP BY 
        vtm.nm,
        rx.name
    ORDER BY items DESC
    """
)

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
        y_title = "Chemical Substance",
        x_title = "Items",
    )

    if selected_category:

        if selected_category == "Other":
            kept_categories = set(
                combined_df.loc[combined_df["vtm_name"] != "Other", "vtm_name"]
            )

            filtered_df = (
                aware_details_breakdown_df[
                    ~aware_details_breakdown_df["vtm_name"].isin(kept_categories)
                ]
                .drop(columns="vtm_name")
                .sort_values("items", ascending=False)
            )

        else:
            filtered_df = (
                aware_details_breakdown_df[
                    aware_details_breakdown_df["vtm_name"] == selected_category
                ]
                .drop(columns="vtm_name")
                .sort_values("items", ascending=False)
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
            },
        )

# show changelog
changelog(Path(__file__).parent)