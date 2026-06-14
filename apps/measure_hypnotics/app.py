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
    return query(f"SELECT DISTINCT date FROM {tool_name}_hypnotic_prescribing ORDER BY date ASC")["date"].tolist()


# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of new visualisations for our measure on Hypnotic and Anxiolytic Average Daily Quantities (ADQs).
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
    st.markdown("### Total oral hypnotic & anxiolytic ADQ per 1000 patients")


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
    table_name=f"{tool_name}_hypnotic_prescribing",
    value_col="total_adq",
    denom_table="list_size",
    denom_col="total"
)

deciles_df = load_deciles(measure_df)
practice_df = load_practice_df() # get data from cascade filter

decile_level = "icb" if level == "national" else level #sets the level of deciles being shown - if nothing selected, shows ICB level deciles
deciles_filtered = deciles_df[deciles_df["org_type"] == decile_level] # filters the deciles to the correct level filtered in the cascade 
measure_filtered = filter_rates(measure_df, level, selected_practice_codes, practice_df) # filters the measure to the correct level

chart_title = "Hypnotic and anxiolytic Average Daily Quantity (ADQ) per 1000 patients" # create chart title
plot_decile_chart(deciles_filtered, level, measure_filtered, measure_name=chart_title, y_format=".1f", y_title="OME per 1000 patients (mg)") # plots decile charts



with st.expander(
    "Click here to see a stacked time chart of anxiolyics and hypnotics",
    icon=":material/stacked_line_chart:",
):


    stacked_df = query(f"""
        SELECT
            date,
            vtm_id,
            vtm_name,
            SUM(total_adq) AS total_adq
        FROM {tool_name}_hypnotic_prescribing AS rx
        WHERE rx.practice_code IN {sql_in}
        GROUP BY
            date,
                        vtm_id,
            vtm_name
        ORDER BY total_adq DESC
    """)

    stacked_df = combine_small_categories_by_date(
        stacked_df,
        date_col="date",
        category_col="vtm_name",
        value_col="total_adq",
        threshold=combine_threshold,
    )


    plot_stacked_area(
        stacked_df,
        x_col="date",
        y_col="total_adq",
        color_col="vtm_name",
        y_title="Total ADQ"
    )

with st.expander(
    f"Click here to see a breakdown of drugs prescribed between {start_date.strftime('%b %Y')} and {end_date.strftime('%b %Y')}", icon=":material/donut_large:"
):
    st.info("""
        Click on drug in bar or donut chart to see breakdown by presentation.

        You can change the date range by using the slide in the sidebar.
        """
    )

    details_df = query(
    f"""
    SELECT
        vtm.nm AS vtm_name,
        SUM(total_adq) AS total_adq 
    FROM {tool_name}_hypnotic_prescribing AS rx
    INNER JOIN medications
    ON rx.snomed_code = medications.id
    INNER JOIN vtm
    ON
    medications.vtm_id = vtm.vtmid
    WHERE date BETWEEN '{start_date}' AND '{end_date}'
    AND rx.practice_code IN {sql_in}
    GROUP BY 
    vtm.nm 
    """
)

    details_breakdown_df = query(
        f"""
        SELECT
            rx.name AS name,
            vtm.nm AS vtm_name,
            SUM(quantity) AS quantity,
            SUM(items) AS items,
            SUM(total_adq) AS total_adq 
        FROM {tool_name}_hypnotic_prescribing AS rx
        INNER JOIN medications
        ON rx.snomed_code = medications.id
        INNER JOIN vtm
        ON
        medications.vtm_id = vtm.vtmid
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND rx.practice_code IN {sql_in}
        GROUP BY 
            vtm.nm,
            rx.name
        ORDER BY items DESC
        """
    )

    chart_type = breakdown_chart_type_selector()

    combined_df = combine_small_categories(
        details_df,
        category_col="vtm_name",
        value_col="total_adq",
        threshold=combine_threshold,
    )

    selected_category = plot_breakdown_chart(
        combined_df,
        value_col="total_adq",
        category_col="vtm_name",
        chart_type=chart_type,
        y_title="Chemical Substance",
        x_title="Total ADQ"
    )

    if selected_category:

        if selected_category == "Other":
            kept_categories = set(
                combined_df.loc[combined_df["vtm_name"] != "Other", "vtm_name"]
            )

            filtered_df = (
                details_breakdown_df[
                    ~details_breakdown_df["vtm_name"].isin(kept_categories)
                ]
                .drop(columns="vtm_name")
                .sort_values("total_adq", ascending=False)
            )
        else:
            filtered_df = (
                details_breakdown_df[
                    details_breakdown_df["vtm_name"] == selected_category
                ]
                .drop(columns=["vtm_name"])
                .sort_values("total_adq", ascending=False)
            )

        filtered_df["percent_adq"] = filtered_df["total_adq"] / filtered_df["total_adq"].sum() * 100

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
                "total_adq": st.column_config.NumberColumn(
                    "Total ADQ",
                    format="%,.1f",
                ),
                "percent_adq": st.column_config.NumberColumn(
                    f"Percent of ADQ for {selected_category}",
                    format="%.1f%%",
                ),
            },
        )

# show changelog
changelog(Path(__file__).parent)