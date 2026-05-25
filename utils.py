import streamlit as st
import pandas as pd
from pathlib import Path
import re
from db import query 



def sidebar_logo():
    st.logo(Path("content/OpenPrescribing_workbench.svg"))
    st.markdown("""
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
        """, unsafe_allow_html=True)


def sidebar_nav():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,100..900;1,100..900&display=swap');

        html, body, p, div, h1, h2, h3, h4, h5, h6, li, a, button, input, label {
            font-family: 'Public Sans', sans-serif !important;
        }

        /* Hide default nav and replace with expander */
        [data-testid="stSidebarNav"] {display: none;}

        /* Remove sidebar padding globally */
        [data-testid="stSidebar"] > div:first-child {
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            padding-top: 0rem !important;
        }

        /* Remove expander content indent */
        [data-testid="stExpanderDetails"] {
            padding-left: 0rem !important;
            padding-right: 0rem !important;
        }

        /* Remove expander label indent */
        [data-testid="stExpander"] summary {
            padding-left: 0rem !important;
        }

        /* Bigger expander label text */
        [data-testid="stExpander"] summary p {
            font-size: 1.1rem !important;
            font-weight: 500 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("&nbsp;" * 3, unsafe_allow_html=True)
        st.divider()
        with st.expander("More Tools", expanded=False, icon=":material/handyman:"):
            st.page_link("pages/home.py", label="Home page")
            st.page_link("apps/tariff_price_changes/tariff_price_changes.py", label="Tariff Price Changes")
            st.page_link("pages/prescribing_topx.py", label="Top x Prescribing")



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
        s = re.sub(r"[A-Za-z]+('[A-Za-z]+)*", lambda m: m.group(0).capitalize(), s) #allows for correct capitalisation of aphostrophes
        replacements = {
            "Gp": "GP", "Nhs": "NHS", "Pcn": "PCN",
            "Icb": "ICB", " And ": " & ",
        }
        for original, clean in replacements.items():
            s = s.replace(original, clean)
        if org_type == "icb":
            s = s.replace(" Integrated Care Board", "").strip() + " ICB"
        if org_type == "reg":
            s = s.replace(" Commissioning Region", "").strip()
        return s

    df["practice_name"] = df["practice_name"].apply(clean_org_name)
    df["pcn_name"]      = df["pcn_name"].apply(clean_org_name)
    df["icb_name"]      = df["icb_name"].apply(lambda s: clean_org_name(s, "icb"))
    df["region_name"]   = df["region_name"].apply(lambda s: clean_org_name(s, "reg"))

    return df


def _cascading_filter(df, col, label, key):
    opts = sorted(df[col].dropna().unique().tolist())
    sel = [v for v in st.session_state.get(key, []) if v in opts]
    sel = st.multiselect(label, opts, default=sel, key=key)
    return df if not sel else df[df[col].isin(sel)]


def org_filter_sidebar():
    df = load_practice_df()

    with st.sidebar:
        with st.expander("Organisation Filter", expanded=False, icon=":material/corporate_fare:"):
            st.info("Select an organisation at any level.")

            df = _cascading_filter(df, "region_name",   "Region",   "sel_region")
            df = _cascading_filter(df, "icb_name",      "ICB",      "sel_icb")
            df = _cascading_filter(df, "pcn_name",      "PCN",      "sel_pcn")
            df = _cascading_filter(df, "practice_name", "Practice", "sel_practice")

    practice_codes = df["practice_code"].drop_duplicates().tolist()
    
    sql_in = "(" + ",".join(f"'{c}'" for c in practice_codes) + ")"
    
    return practice_codes, sql_in

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