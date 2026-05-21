import streamlit as st
import re
from db import query 


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
        st.header("Organisation Filter")
        st.info("Select an organisation at any level.")

        df = _cascading_filter(df, "region_name",   "Region",   "sel_region")
        df = _cascading_filter(df, "icb_name",      "ICB",      "sel_icb")
        df = _cascading_filter(df, "pcn_name",      "PCN",      "sel_pcn")
        df = _cascading_filter(df, "practice_name", "Practice", "sel_practice")

    selected_practices = df["practice_code"].drop_duplicates().tolist()

    if len(selected_practices) == 1:
        return f"('{selected_practices[0]}')"

    return str(tuple(selected_practices))