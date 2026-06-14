import streamlit as st
import altair as alt
import pandas as pd
from utils import get_filter_label


def plot_decile_chart(deciles_df, level, rates_df=None, measure_name=None, y_format="%", y_title="Rate"):
    OP_COLOURS = [
        "#e41a1c", "#ff7f00", "#4daf4a", "#984ea3", "#a65628",
        "#f781bf", "#999999", "#b15928", "#66c2a5", "#fc8d62",
        "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494",
        "#b3b3b3", "#1b9e77", "#d95f02", "#7570b3", "#e7298a"
    ]

    if measure_name:
        filter_label = get_filter_label()
        label = f"{measure_name} in {filter_label}"
        st.markdown(f"#### {label}")

    y_axis = alt.Y(
        "rate:Q",
        title=y_title,
        axis=alt.Axis(format=y_format),
        scale=alt.Scale(zero=False),
       
    )

    chart_type = st.radio(
        "",
        options=["deciles", "range"],
        format_func=lambda x: {
            "deciles": "Show deciles",
            "range": "Show interquartile range & 1st-9th deciles",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
    )

    if chart_type == "deciles":
        decile_cols = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9"]
        df_long = deciles_df.melt(
            id_vars=["date", "org_type"],
            value_vars=decile_cols,
            var_name="decile",
            value_name="rate",
        )

        df_deciles = df_long[df_long["decile"] != "d5"]
        df_median = df_long[df_long["decile"] == "d5"]

        decile_layer = (
            alt.Chart(df_deciles)
            .mark_line(color="steelblue", strokeDash=[2, 4], size=1)
            .encode(
                x=alt.X('date:T', title='Month',axis=alt.Axis(format='%b %Y', tickCount=alt.TimeIntervalStep('month', 3))),
                y=y_axis,
                detail="decile:N",
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
        outer_band = (
            alt.Chart(deciles_df)
            .mark_area(opacity=0.2, color="steelblue")
            .encode(
                x=alt.X('date:T', title='Month',axis=alt.Axis(format='%b %Y', tickCount=alt.TimeIntervalStep('month', 3))),
                y=alt.Y(
                    "d1:Q",
                    title=y_title,
                    axis=alt.Axis(format=y_format),
                    scale=alt.Scale(zero=False),
                ),
                y2=alt.Y2("d9:Q"),
            )
        )

        inner_band = (
            alt.Chart(deciles_df)
            .mark_area(opacity=0.4, color="steelblue")
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("q25:Q", scale=alt.Scale(zero=False)),
                y2=alt.Y2("q75:Q"),
            )
        )

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
        if level == "national":
            line_layer = (
                alt.Chart(rates_df)
                .mark_line(size=2, color="red")
                .encode(
                    x=alt.X("date:T"),
                    y=y_axis,
                )
            )
            point_layer = (
                alt.Chart(rates_df)
                .mark_point(size=40, filled=True, color="red")
                .encode(
                    x=alt.X("date:T"),
                    y=y_axis,
                )
            )
        else:
            level_col = {
                "practice": "practice_code",
                "pcn": "pcn_code",
                "icb": "icb_code",
                "region": "region_code",
            }[level]

            name_col = level_col.replace("_code", "_name")

            line_layer = (
                alt.Chart(rates_df)
                .mark_line(size=2)
                .encode(
                    x=alt.X("date:T"),
                    y=y_axis,
                    color=alt.Color(
                        f"{name_col}:N",
                        scale=alt.Scale(range=OP_COLOURS),
                        legend=alt.Legend(title=None),
                    ),
                    detail=f"{name_col}:N",
                )
            )

            point_layer = (
                alt.Chart(rates_df)
                .mark_point(size=40, filled=True)
                .encode(
                    x=alt.X("date:T"),
                    y=y_axis,
                    color=alt.Color(
                        f"{name_col}:N",
                        scale=alt.Scale(range=OP_COLOURS),
                        legend=alt.Legend(title=None),
                    ),
                    detail=f"{name_col}:N",
                )
            )

        chart = chart + line_layer + point_layer

    st.altair_chart(chart, width="stretch")


def plot_stacked_area(
    stacked_df,
    x_col,
    y_col,
    color_col,
    y_title,
    sort_order=None,
):
    chart = (
        alt.Chart(stacked_df)
        .mark_area()
        .encode(
            x=alt.X(f"{x_col}:T", title="Month",axis=alt.Axis(format='%b %Y', tickCount=alt.TimeIntervalStep('month', 3))),
            y=alt.Y(f"{y_col}:Q", title=y_title,stack=True),
            color=alt.Color(
                f"{color_col}:N",
                sort=sort_order,
                legend=alt.Legend(title=None),
            ),
        )
    )

    st.altair_chart(chart, width="stretch")


def breakdown_chart_type_selector(
    label="Chart type",
    options=("bar", "donut"),
    horizontal=True,
    key="chart_type",
):
    return st.radio(
        label,
        options,
        horizontal=horizontal,
        key=key,
    )


def plot_breakdown_chart(
    data_df: pd.DataFrame,
    value_col: str,
    category_col: str,
    chart_type: str = "bar",
    key: str | None = None,
    y_title: str = "Name",
    x_title: str = "",
):
    selection_param = alt.selection_point(
        name="my_selection",
        fields=[category_col],
    )

    base = alt.Chart(data_df)

    theta = alt.Theta(f"{value_col}:Q", stack=True)

    if chart_type == "donut":
        chart = (
            base
            .transform_joinaggregate(total=f"sum({value_col})")
            .transform_calculate(
                pct=f"format(datum['{value_col}'] / datum.total * 100, '.1f') + '%'"
            )
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta(f"{value_col}:Q"),
                color=alt.Color(
                    f"{category_col}:N",
                    legend=alt.Legend(title=None),
                ),
                tooltip=[
                    alt.Tooltip(f"{category_col}:N", title="Drug"),
                    alt.Tooltip("pct:N", title="Share"),
                ],
            )
            .add_params(selection_param)
        )

    else:
        chart = (
            base.mark_bar()
            .encode(
                x=alt.X(f"{value_col}:Q", title=x_title),
                y=alt.Y(f"{category_col}:N", sort="-x", axis=alt.Axis(labelLimit=500),title=y_title),
                color=alt.Color(
                    f"{category_col}:N",
                    legend=None,
                ),
            )
            .add_params(selection_param)
        )

    chart_selection = st.altair_chart(
        chart,
        on_select="rerun",
        width="stretch",
        key=key,
    )
    if chart_selection.selection.my_selection:
        return chart_selection.selection.my_selection[0][category_col]

    return None

def plot_improvement_chart(deciles_df, org_df):
    y_axis = alt.Y("rate:Q", title="Rate", scale=alt.Scale(zero=False))

    decile_df = deciles_df[deciles_df["percentile"] != 0.5]
    median_df = deciles_df[deciles_df["percentile"] == 0.5]

    decile_layer = (
        alt.Chart(decile_df)
        .mark_line(color="steelblue", strokeDash=[2, 4], size=1)
        .encode(
            x=alt.X("month:T", title="Month", axis=alt.Axis(format="%b %Y", tickCount=alt.TimeIntervalStep("month", 3))),
            y=y_axis,
            detail="percentile:Q",
        )
    )

    median_layer = (
        alt.Chart(median_df)
        .mark_line(color="steelblue", strokeDash=[8, 4], size=2)
        .encode(
            x=alt.X("month:T"),
            y=y_axis,
        )
    )

    org_layer = (
        alt.Chart(org_df)
        .mark_line(size=2)
        .encode(
            x=alt.X("month:T"),
            y=alt.Y("calc_value:Q", scale=alt.Scale(zero=False)),
            color=alt.Color("sicbl_name:N", legend=alt.Legend(title=None)),
        )
    )

    chart = decile_layer + median_layer + org_layer
    st.altair_chart(chart, use_container_width=True)