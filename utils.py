import re
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from db import query


def sidebar_logo():
    st.logo(Path("content/OpenPrescribing_workbench.svg"))
    st.markdown(
        """
        <style>
        [data-testid="stLogoLink"] {
            height: auto !important;
            min-height: auto !important;
        }

        [data-testid="stSidebarLogo"] {
            height: 20rem !important;
            max-height: unset !important;
            margin-top: 3rem !important;
        }

        [data-testid="stLogoLink"] button {
            height: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def global_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,100..900;1,100..900&display=swap');

        html, body, p, div, h1, h2, h3, h4, h5, h6, li, a, button, input, label {
            font-family: 'Public Sans', sans-serif !important;
        }

        [data-testid="stSidebarNav"] {display: none;}

        [data-testid="stSidebar"] > div:first-child {
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            padding-top: 0rem !important;
        }

        [data-testid="stExpanderDetails"] {
            padding-left: 0rem !important;
            padding-right: 0rem !important;
        }

        [data-testid="stExpander"] summary {
            padding-left: 0rem !important;
        }

        [data-testid="stExpander"] summary p {
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }

        details {
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] details {
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary {
            border-radius: 0.5rem !important;
        }

        [data-testid="stDataFrame"] td {
            border: none !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    with st.sidebar:
        st.markdown("&nbsp;" * 3, unsafe_allow_html=True)
        st.divider()
        with st.expander("More Tools", expanded=False, icon=":material/handyman:"):
            st.page_link("pages/home.py", label="Home page")
            st.page_link(
                "apps/tariff_price_changes/app.py", label="Tariff Price Changes"
            )
            st.page_link("apps/prescribing_topx/app.py", label="Top x Prescribing")
            st.page_link("apps/measure_aware/app.py", label="Measure: aWaRe")
            st.page_link(
                "apps/measure_hypnotics/app.py",
                label="Measure: Hypnotics & Anxiolytics",
            )
            st.page_link("apps/measure_ome/app.py", label="Measure: Opioids OME")

            # st.page_link("apps/gbg/app.py", label="Ghost Branded Generics")
            (st.page_link("apps/improvement_radar/app.py", label="Improvement Radar"),)
        st.divider()
        with st.expander("Developer Tools", expanded=False, icon=":material/build:"):
            st.page_link("pages/db_schema.py", label="Database schema")
            st.page_link("pages/sql_checker.py", label="Code tests")
            st.page_link("apps/forecasting/app.py", label="Forecasting")
            st.page_link("apps/measure_denosumab/app.py", label="Measure - denosumab")
            st.page_link("apps/growth/app.py", label="Measure: Growth")


@st.cache_data
def load_practice_df():
    df = query("""
        SELECT
            prac.id AS practice_code,
            prac.name AS practice_name,
            MAX(CASE WHEN par.org_type = 'pcn' THEN par.id END) AS pcn_code,
            MAX(CASE WHEN par.org_type = 'pcn' THEN par.name END) AS pcn_name,
            MAX(CASE WHEN par.org_type = 'icb' THEN par.id END) AS icb_code,
            MAX(CASE WHEN par.org_type = 'icb' THEN par.name END) AS icb_name,
            MAX(CASE WHEN par.org_type = 'reg' THEN par.id END) AS region_code,
            MAX(CASE WHEN par.org_type = 'reg' THEN par.name END) AS region_name
        FROM org AS prac
        INNER JOIN org_relation AS rel
            ON prac.id = rel.child_id
        INNER JOIN org AS par
             ON rel.parent_id = par.id
        WHERE prac.org_type = 'pra'
        AND prac.inactive = 0
        GROUP BY prac.id, prac.name
    """)

    ### tidy organisation names to fit better in filter
    def clean_org_name(s, org_type=None):
        if not isinstance(s, str):
            return s
        s = re.sub(
            r"[A-Za-z]+('[A-Za-z]+)*", lambda m: m.group(0).capitalize(), s
        )  # allows for correct capitalisation of aphostrophes
        replacements = {
            "Gp": "GP",
            "Nhs": "NHS",
            "Pcn": "PCN",
            "Icb": "ICB",
            " And ": " & ",
        }
        for original, clean in replacements.items():
            s = s.replace(original, clean)
        if org_type == "icb":
            s = s.replace(" Integrated Care Board", "").strip() + " ICB"
        if org_type == "reg":
            s = s.replace(" Commissioning Region", "").strip()
        return s

    df["practice_name"] = df["practice_name"].apply(clean_org_name)
    df["pcn_name"] = df["pcn_name"].apply(clean_org_name)
    df["icb_name"] = df["icb_name"].apply(lambda s: clean_org_name(s, "icb"))
    df["region_name"] = df["region_name"].apply(lambda s: clean_org_name(s, "reg"))

    return df


def _cascading_filter(df, col, label, key):
    opts = sorted(df[col].dropna().unique().tolist())
    sel = [v for v in st.session_state.get(key, []) if v in opts]
    sel = st.multiselect(label, opts, default=sel, key=key)
    return df if not sel else df[df[col].isin(sel)]


def org_filter_sidebar():
    df = load_practice_df()

    with st.sidebar:
        with st.expander(
            "Organisation Filter", expanded=False, icon=":material/corporate_fare:"
        ):
            st.info("Select an organisation at any level.")

            df = _cascading_filter(df, "region_name", "Region", "sel_region")
            df = _cascading_filter(df, "icb_name", "ICB", "sel_icb")
            df = _cascading_filter(df, "pcn_name", "PCN", "sel_pcn")
            df = _cascading_filter(df, "practice_name", "Practice", "sel_practice")

            level = "national"  # default when nothing selected
            for lvl, key in [
                ("practice", "sel_practice"),
                ("pcn", "sel_pcn"),
                ("icb", "sel_icb"),
                ("region", "sel_region"),
            ]:
                if st.session_state.get(key):
                    level = lvl
                    break

    practice_codes = df["practice_code"].drop_duplicates().tolist()
    sql_in = "(" + ",".join(f"'{c}'" for c in practice_codes) + ")"

    return practice_codes, sql_in, level


def get_filter_label():
    for key, label_col in [
        ("sel_practice", "practice_name"),
        ("sel_pcn", "pcn_name"),
        ("sel_icb", "icb_name"),
        ("sel_region", "region_name"),
    ]:
        vals = st.session_state.get(key, [])
        if vals:
            return ", ".join(vals)
    return "England"


@st.cache_data
def load_proportion_rates(
    table_name, value_col, numerator_condition, denominator_condition=None
):
    denom = (
        f"CASE WHEN {denominator_condition} THEN {value_col} ELSE 0 END"
        if denominator_condition
        else value_col
    )

    return query(f"""
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
        )
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
            SUM(CASE WHEN {numerator_condition} THEN {value_col} ELSE 0 END) AS numerator,
            SUM({denom}) AS denominator,
            numerator / NULLIF(denominator, 0) AS rate
        FROM {table_name} AS rx
        JOIN orgs AS o ON rx.practice_code = o.practice_code
        GROUP BY GROUPING SETS (
            (date, o.practice_code),
            (date, o.pcn_code),
            (date, o.icb_code),
            (date, o.region_code)
        )
    """)


@st.cache_data
def load_per1000_rates(
    table_name,
    value_col,
    denom_table,
    denom_col,
    numerator_condition=None,
    scale=1000.0,
):
    numer = (
        f"CASE WHEN {numerator_condition} THEN {value_col} ELSE 0 END"
        if numerator_condition
        else value_col
    )
    org_type = """
        CASE
            WHEN o.practice_code IS NOT NULL THEN 'practice'
            WHEN o.pcn_code      IS NOT NULL THEN 'pcn'
            WHEN o.icb_code      IS NOT NULL THEN 'icb'
            WHEN o.region_code   IS NOT NULL THEN 'region'
        END
    """

    return query(f"""
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
        n AS (
            SELECT
                rx.date,
                o.practice_code,
                o.pcn_code,
                o.icb_code,
                o.region_code,
                {org_type} AS org_type,
                SUM({numer}) AS numerator
            FROM {table_name} AS rx
            JOIN orgs AS o ON rx.practice_code = o.practice_code
            GROUP BY GROUPING SETS (
                (rx.date, o.practice_code),
                (rx.date, o.pcn_code),
                (rx.date, o.icb_code),
                (rx.date, o.region_code)
            )
        ),
        d AS (
            SELECT
                dd.date,
                o.practice_code,
                o.pcn_code,
                o.icb_code,
                o.region_code,
                {org_type} AS org_type,
                SUM(dd.{denom_col}) / {scale} AS denominator
            FROM {denom_table} AS dd
            JOIN orgs AS o ON dd.practice_code = o.practice_code
            GROUP BY GROUPING SETS (
                (dd.date, o.practice_code),
                (dd.date, o.pcn_code),
                (dd.date, o.icb_code),
                (dd.date, o.region_code)
            )
        )
        SELECT
            n.date,
            n.practice_code,
            n.pcn_code,
            n.icb_code,
            n.region_code,
            n.org_type,
            n.numerator,
            d.denominator,
            n.numerator / NULLIF(d.denominator, 0) AS rate
        FROM n
        JOIN d
          ON n.date = d.date
         AND n.org_type = d.org_type
         AND COALESCE(n.practice_code, n.pcn_code, n.icb_code, n.region_code)
           = COALESCE(d.practice_code, d.pcn_code, d.icb_code, d.region_code)
    """)


def load_deciles(rates_df):
    return (
        rates_df.groupby(["date", "org_type"])["rate"]
        .quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.25, 0.75])
        .unstack()
        .reset_index()
        .rename(
            columns={
                0.1: "d1",
                0.2: "d2",
                0.3: "d3",
                0.4: "d4",
                0.5: "d5",
                0.6: "d6",
                0.7: "d7",
                0.8: "d8",
                0.9: "d9",
                0.25: "q25",
                0.75: "q75",
            }
        )
    )


def filter_rates(rates_df, level, selected_practice_codes, practice_df):
    if level == "national":
        national = (
            rates_df[rates_df["org_type"] == "practice"]
            .groupby("date")[["numerator", "denominator"]]
            .sum()
            .reset_index()
        )
        national["rate"] = national["numerator"] / national["denominator"].replace(
            0, pd.NA
        )
        national["org_type"] = "national"
        national["label"] = "National"
        return national

    level_col = {
        "practice": "practice_code",
        "pcn": "pcn_code",
        "icb": "icb_code",
        "region": "region_code",
    }[level]

    name_col = level_col.replace("_code", "_name")

    selected_orgs = (
        practice_df[practice_df["practice_code"].isin(selected_practice_codes)][
            level_col
        ]
        .dropna()
        .unique()
        .tolist()
    )

    filtered = rates_df[
        (rates_df["org_type"] == level) & (rates_df[level_col].isin(selected_orgs))
    ]

    name_lookup = practice_df[[level_col, name_col]].drop_duplicates()

    return filtered.merge(name_lookup, on=level_col, how="left")


def gbp(x, dp=0):
    """Format a value as GBP."""
    if pd.isna(x):
        return ""

    x = float(x)
    sign = "-" if x < 0 else ""

    return f"{sign}£{abs(x):,.{dp}f}"


def render_pagination(sorted_df, render_row, page_size=20):
    if "page" not in st.session_state:
        st.session_state.page = 0

    total_pages = max(1, (len(sorted_df) - 1) // page_size + 1)
    if st.session_state.page >= total_pages:
        st.session_state.page = 0

    page = st.session_state.page
    page_df = sorted_df.iloc[page * page_size : (page + 1) * page_size]

    for _, row in page_df.iterrows():
        render_row(row)

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


def changelog(base_path: Path, expanded: bool = False):
    st.divider()

    with open(base_path / "content/changelog.yaml") as f:
        data = yaml.safe_load(f)

    with st.expander(
        "Click to see changelog", icon=":material/history:", expanded=expanded
    ):
        for entry in reversed(data):
            st.markdown(
                f"**{entry['date']}** — {entry['change']} *({entry['person']})*"
            )


def why_it_matters(base_path: Path, expanded: bool = True):
    with (
        st.expander("Why It Matters", icon=":material/admin_meds:", expanded=expanded),
        open(base_path / "content/why_it_matters.md") as f,
    ):
        st.markdown(f.read())


def combine_threshold_slider(
    label="Combine chemicals below (%) to 'Other'",
    min_value=0,
    max_value=10,
    default=2,
    step=1,
    expanded=False,
):
    with st.sidebar.expander(
        "Combine low use drugs", icon=":material/merge:", expanded=expanded
    ):
        return (
            st.slider(
                label,
                min_value=min_value,
                max_value=max_value,
                value=default,
                step=step,
            )
            / 100
        )


def combine_small_categories(
    df,
    category_col,
    value_col,
    threshold=0.02,
    other_label="Other",
):
    df = df.copy()

    total = df[value_col].sum()
    category_totals = df.groupby(category_col)[value_col].transform("sum")
    keep_mask = category_totals / total >= threshold

    df[category_col] = df[category_col].where(keep_mask, other_label)

    return (
        df.groupby(category_col, as_index=False)[value_col]
        .sum()
        .sort_values(value_col, ascending=False)
    )


def combine_small_categories_by_date(
    df,
    date_col,
    category_col,
    value_col,
    threshold=0.02,
    other_label="Other",
):
    df = df.copy()

    total = df[value_col].sum()
    category_totals = df.groupby(category_col)[value_col].transform("sum")
    keep_mask = category_totals / total >= threshold

    df[category_col] = df[category_col].where(keep_mask, other_label)

    return (
        df.groupby([date_col, category_col], as_index=False)[value_col]
        .sum()
        .sort_values(value_col, ascending=False)
    )
