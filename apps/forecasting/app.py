import streamlit as st
from pathlib import Path
import pandas as pd
import yaml
import altair as alt
import duckdb
import time

from db import query
from utils import sidebar_logo, sidebar_nav, org_filter_sidebar,gbp, render_pagination, global_styles, changelog, why_it_matters, load_proportion_rates, load_deciles, filter_rates, load_practice_df, combine_threshold_slider, combine_small_categories
from charts import plot_decile_chart, plot_stacked_area,     breakdown_chart_type_selector,     plot_breakdown_chart

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---

tool_name = Path(__file__).parent.name # defines the tool name
app_path = Path(__file__).parent

# --- Functions ---

def ensure_extensions():
    con = duckdb.connect()
    con.execute("INSTALL anofox_forecast FROM community")
    con.close()

# --- Data ---




# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of understanding forecasting!
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)



ensure_extensions()

import pandas as pd
import time

icb_codes = query(f"""
    SELECT DISTINCT split_part(unique_id, '_', 1) AS icb_code
    FROM {tool_name}_forecasting
    ORDER BY icb_code
""")["icb_code"].tolist()

all_forecasts = []
timings = []

with st.spinner(f"Running forecast across {len(icb_codes)} ICBs..."):
    progress = st.progress(0)
    overall_start = time.perf_counter()

    for i, icb in enumerate(icb_codes):
        icb_start = time.perf_counter()

        chunk = query(f"""
            CREATE OR REPLACE TEMP TABLE ts_train_chunk AS
            SELECT unique_id, ds, y
            FROM {tool_name}_forecasting
            WHERE unique_id LIKE '{icb}\\_%' ESCAPE '\\'
              AND ds >= DATE '2025-11-01' - INTERVAL 3 YEAR
              AND ds <= DATE '2025-11-01';

            SELECT * FROM ts_forecast_by(
                'ts_train_chunk', unique_id, ds, y,
                'AutoARIMA', 4, '1mo',
                MAP{{'seasonal_period': '12'}}
            );
        """)

        icb_elapsed = time.perf_counter() - icb_start
        chunk["icb_code"] = icb
        all_forecasts.append(chunk)
        timings.append({"icb_code": icb, "seconds": icb_elapsed})

        progress.progress((i + 1) / len(icb_codes))

forecast = pd.concat(all_forecasts, ignore_index=True)
overall_elapsed = time.perf_counter() - overall_start

timing_df = pd.DataFrame(timings).sort_values("seconds", ascending=False)
st.write(f"Total: {overall_elapsed:.1f}s across {len(icb_codes)} ICBs")
st.dataframe(timing_df)

forecast[["icb_code", "snomed_code"]] = forecast["unique_id"].str.split("_", n=1, expand=True)

icb_check = forecast[forecast["icb_code"] == "QJK"]

st.write(icb_check)

import altair as alt
import pandas as pd

icb = "QJK"
cutoff = "2025-11-01"

forecast_icb = forecast[forecast["icb_code"] == icb]

top50 = query(f"""
    SELECT unique_id, SUM(y) AS total_y
    FROM {tool_name}_forecasting
    WHERE unique_id LIKE '{icb}\\_%' ESCAPE '\\'
      AND ds >= DATE '{cutoff}' - INTERVAL 3 YEAR
      AND ds <= DATE '{cutoff}'
    GROUP BY unique_id
    ORDER BY total_y DESC
    LIMIT 50
""")

actuals_full = query(f"""
    SELECT unique_id, ds, y AS actual_y
    FROM {tool_name}_forecasting
    WHERE unique_id LIKE '{icb}\\_%' ESCAPE '\\'
""")

comparison = (
    actuals_full
    .merge(
        forecast_icb[["unique_id", "ds", "yhat"]],
        on=["unique_id", "ds"],
        how="left",
    )
)

comparison = comparison[comparison["unique_id"].isin(top50["unique_id"])]

st.dataframe(comparison)

chart_data = comparison.melt(
    id_vars=["unique_id", "ds"],
    value_vars=["actual_y", "yhat"],
    var_name="series",
    value_name="value",
)

charts = []
for uid in comparison["unique_id"].unique():
    subset = chart_data[chart_data["unique_id"] == uid]

    chart = (
        alt.Chart(subset)
        .mark_line()
        .encode(
            x=alt.X("ds:T", title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("value:Q", title=None),
            color=alt.Color(
                "series:N",
                scale=alt.Scale(
                    domain=["actual_y", "yhat"],
                    range=["#1f77b4", "#d62728"],
                ),
                legend=None,
            ),
        )
        .properties(width=180, height=140, title=uid)
    )
    charts.append(chart)

n_cols = 5
rows = [
    alt.hconcat(*charts[i : i + n_cols])
    for i in range(0, len(charts), n_cols)
]
grid = alt.vconcat(*rows)

st.altair_chart(grid, use_container_width=False)