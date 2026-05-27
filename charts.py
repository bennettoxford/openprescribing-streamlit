import streamlit as st
import altair as alt
import pandas as pd

def plot_decile_chart(deciles_df, level, rates_df=None):

    OP_COLOURS = [
        "#e41a1c", "#ff7f00", "#4daf4a", "#984ea3", "#a65628",
        "#f781bf", "#999999", "#b15928", "#66c2a5", "#fc8d62",
        "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494",
        "#b3b3b3", "#1b9e77", "#d95f02", "#7570b3", "#e7298a"
    ]

    y_axis = alt.Y("rate:Q", title="Rate", axis=alt.Axis(format="%"), scale=alt.Scale(zero=False))

    chart_type = st.radio(
        "Chart type",
        ["Show deciles", "Show ranges"],
        horizontal=True
    )

    if chart_type == "Show deciles":
        decile_cols = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "d10"]
        df_long = deciles_df.melt(
            id_vars=["date", "org_type"],
            value_vars=decile_cols,
            var_name="decile",
            value_name="rate"
        )

        df_deciles = df_long[df_long["decile"] != "d5"]
        df_median  = df_long[df_long["decile"] == "d5"]

        decile_layer = (
            alt.Chart(df_deciles)
            .mark_line(color="steelblue", strokeDash=[2, 4], size=1)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=y_axis,
                detail="decile:N"
            )
        )

        median_layer = (
            alt.Chart(df_median)
            .mark_line(color="steelblue", strokeDash=[8, 4], size=2)
            .encode(
                x=alt.X("date:T"),
                y=y_axis,
            )
        )

        chart = decile_layer + median_layer

    else:
        # outer band: 10th-90th
        outer_band = (
            alt.Chart(deciles_df)
            .mark_area(opacity=0.2, color="steelblue")
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("d1:Q", title="Rate", axis=alt.Axis(format="%"), scale=alt.Scale(zero=False)),
                y2=alt.Y2("d9:Q")
            )
        )

        # inner band: 25th-75th
        inner_band = (
            alt.Chart(deciles_df)
            .mark_area(opacity=0.4, color="steelblue")
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("q25:Q", scale=alt.Scale(zero=False)),
                y2=alt.Y2("q75:Q")
            )
        )

        # median line
        median_layer = (
            alt.Chart(deciles_df)
            .mark_line(color="steelblue", strokeDash=[8, 4], size=2)
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("d5:Q", scale=alt.Scale(zero=False)),
            )
        )

        chart = outer_band + inner_band + median_layer

    if rates_df is not None:
        level_col = {
            "practice": "practice_code",
            "pcn":      "pcn_code",
            "icb":      "icb_code",
            "region":   "region_code",
        }[level]

        line_layer = (
            alt.Chart(rates_df)
            .mark_line(size=2)
            .encode(
                x=alt.X("date:T"),
                y=y_axis,
                color=alt.Color(f"{level_col}:N", scale=alt.Scale(range=OP_COLOURS)),
                detail=f"{level_col}:N"
            )
        )

        point_layer = (
            alt.Chart(rates_df)
            .mark_point(size=40, filled=True)
            .encode(
                x=alt.X("date:T"),
                y=y_axis,
                color=alt.Color(f"{level_col}:N", scale=alt.Scale(range=OP_COLOURS)),
                detail=f"{level_col}:N"
            )
        )

        chart = chart + line_layer + point_layer

    st.altair_chart(chart, use_container_width=True)