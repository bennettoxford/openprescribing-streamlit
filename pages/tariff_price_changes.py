from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from db import create_materialised_view, query
from org_filter import org_filter_sidebar
from page_formatting import gbp

st.set_page_config(layout="wide")

# Get data sources

create_materialised_view(
    name="tariff_price_changes_01_price_changes"
)  # create main price change table
create_materialised_view(
    name="tariff_price_changes_02_vmpp"
)  # create vmpp detail table
create_materialised_view(
    name="tariff_price_changes_03_prescribing"
)  # create prescribing table
vmpp_df = query("SELECT * FROM tariff_price_changes_02_vmpp")  # creates vmpp df
tariff_df = query(
    "SELECT * FROM tariff_price_changes_01_price_changes"
)  # create main table df
tariff_cat_df = (
    query(
        "SELECT DISTINCT tariff_cat FROM tariff_price_changes_01_price_changes ORDER BY tariff_cat"
    )["tariff_cat"]
    .dropna()
    .tolist()
)
tariff_prescribing_df = query("SELECT * FROM tariff_price_changes_03_prescribing")


def build_price_change_df(vmpp_df):
    """Add numeric price columns and a price_change label to vmpp_df."""
    df = vmpp_df.copy()
    df["price"] = pd.to_numeric(df["price_pence"], errors="coerce")
    df["prev_price"] = pd.to_numeric(df["previous_price_pence"], errors="coerce")
    df = df[df["price"].notna() & df["prev_price"].notna()]
    df["price_change"] = "unchanged"
    df.loc[df["price"] > df["prev_price"], "price_change"] = "increase"
    df.loc[df["price"] < df["prev_price"], "price_change"] = "decrease"
    return df


def render_summary(df):
    """Render a per-category increase/decrease/unchanged summary."""
    summary = (
        df.groupby(["tariff_category", "price_change"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for _, row in summary.iterrows():
        st.markdown(f"**Category: {row['tariff_category']}**")
        c1, c2, c3 = st.columns(3)
        c1.write(f"Increases: {row.get('increase', 0)}")
        c2.write(f"Decreases: {row.get('decrease', 0)}")
        c3.write(f"No change: {row.get('unchanged', 0)}")


def render_pagination(sorted_df):
    """Render paginated expanders for each BNF presentation."""
    if "page" not in st.session_state:
        st.session_state.page = 0

    total_pages = max(1, (len(sorted_df) - 1) // 20 + 1)
    if st.session_state.page >= total_pages:
        st.session_state.page = 0

    page = st.session_state.page
    page20 = sorted_df.iloc[page * 20 : (page + 1) * 20]

    for _, row in page20.iterrows():
        colour = "red" if row["price_difference"] > 0 else "green"
        label = f":{colour}[{row['name']}: {gbp(row['price_difference'], 2)}]"
        vmpp_details = vmpp_df[vmpp_df["vpid"] == row["snomed_code"]].copy()
        with st.expander(label):
            display_df = vmpp_details[
                ["nm", "price_pence", "previous_price_pence", "tariff_category"]
            ].copy()
            display_df["price_pence"] = (
                pd.to_numeric(display_df["price_pence"], errors="coerce") / 100
            ).apply(lambda x: gbp(x, dp=2))
            display_df["previous_price_pence"] = (
                pd.to_numeric(display_df["previous_price_pence"], errors="coerce") / 100
            ).apply(lambda x: gbp(x, dp=2))
            display_df.columns = ["Name", "Price", "Previous Price", "DT Category"]
            st.dataframe(display_df, hide_index=True, use_container_width=True)

    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Previous", disabled=page == 0):
            st.session_state.page -= 1
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center'>Page {page + 1} of {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next →", disabled=page >= total_pages - 1):
            st.session_state.page += 1
            st.rerun()


max_rx_date = query("SELECT MAX(date) FROM date")["max(date)"][0]
max_tariff_date = query("SELECT MAX(date) FROM data_tariffprice")["max(date)"][0]
tariff_month = max_tariff_date.strftime("%B %Y")
rx_month = max_rx_date.strftime("%B %Y")


# App

# Header
st.image(Path("content/OpenPrescribing.svg"))
st.info(
    """##### Hello!  This is a **very** early prototype of estimating the impact of drug tariff changes.
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)"""
)

with st.expander(
    "Click here to read our methodology", icon=":material/quick_reference:"
):
    with open(Path("content/tariff_price_changes/methodology.md")) as f:
        st.markdown(f.read())

# Sidebar filters
with st.sidebar:
    st.markdown(f"### Drug Tariff month: {tariff_month}")
    st.markdown(f"### Prescribing data used for estimate: {rx_month}")

selected_practice_codes = org_filter_sidebar()

with st.sidebar:
    st.header("Tariff Filter")
    sel_tariff_cat = st.multiselect(
        "DT Category",
        ["(All)"] + sorted(tariff_cat_df),
        key="sel_tariff_cat",
    )

    sort_option = st.radio(
        "Sort by",
        ["Largest Increases", "Largest Reductions"],
        key="sort_option",
    )

# Show summary
st.markdown(f"#### Total changes for {tariff_month}")
render_summary(build_price_change_df(vmpp_df))

# Filter rx query
filtered_df = query(
    f"""
    SELECT
        rx.snomed_code,
        med.name,
        dt.tariff_cat,
        SUM(rx.quantity * dt.price_diff_pu * dt.is_max_price_diff_pu) AS price_difference
    FROM tariff_price_changes_03_prescribing AS rx
    INNER JOIN tariff_price_changes_price_changes AS dt ON rx.snomed_code = dt.vpid
    INNER JOIN medications AS med ON rx.snomed_code = med.id
    WHERE practice_code IN {selected_practice_codes}
    GROUP BY
        rx.snomed_code,
        med.name,
        dt.tariff_cat
    """
)

if sel_tariff_cat:
    filtered_df = filtered_df[filtered_df["tariff_cat"].isin(sel_tariff_cat)]

# Show results
total_difference = filtered_df["price_difference"].sum()
st.markdown(f"### Total estimated monthly price difference: {gbp(total_difference, 2)}")

st.markdown("### Breakdown by presentation")
st.info("ℹ️ To see details on changes to individual packs, click on the arrow")
st.markdown(
    """
<style>
details { border: none !important; box-shadow: none !important; }
</style>
""",
    unsafe_allow_html=True,
)
sorted_df = filtered_df.sort_values(
    "price_difference", ascending=(sort_option != "Largest Increases")
)
render_pagination(sorted_df)

# Methodology and changelog

st.divider()

with open(Path("content/tariff_price_changes/changelog.yaml")) as f:
    changelog = yaml.safe_load(f)

with st.expander("Click to see changelog", icon=":material/history:"):
    for entry in reversed(changelog):
        st.markdown(f"**{entry['date']}** — {entry['change']} *({entry['person']})*")
