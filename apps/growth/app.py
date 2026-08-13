from pathlib import Path

import streamlit as st

from db import query
from utils import (
    global_styles,
    sidebar_logo,
)

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
##### Hello!  This is a **very** early prototype of understanding growth in cost and items.
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)

growth = query(
    f"""
    WITH orgs AS (
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
        INNER JOIN org_relation AS rel ON prac.id = rel.child_id
        INNER JOIN org AS par ON rel.parent_id = par.id
        WHERE prac.org_type = 'pra'
        AND prac.inactive = 0
        GROUP BY prac.id, prac.name
    ),
    grouped AS (
        SELECT
            date,
            CASE
                WHEN GROUPING(orgs.practice_code) = 0 THEN 'practice'
                WHEN GROUPING(orgs.pcn_code) = 0 THEN 'pcn'
                WHEN GROUPING(orgs.icb_code) = 0 THEN 'icb'
                WHEN GROUPING(orgs.region_code) = 0 THEN 'region'
                ELSE 'national'
            END AS org_level,
            orgs.practice_code,
            orgs.practice_name,
            orgs.pcn_code,
            orgs.pcn_name,
            orgs.icb_code,
            orgs.icb_name,
            orgs.region_code,
            orgs.region_name,
            subpara,
            SUM(spend_last_12m) AS spend_last_12m,
            SUM(spend_prev_12m) AS spend_prev_12m,
            SUM(items_last_12m) AS items_last_12m,
            SUM(items_prev_12m) AS items_prev_12m
        FROM {tool_name}_growth AS growth
        INNER JOIN orgs ON orgs.practice_code = growth.practice_code
        WHERE date = (SELECT MAX(date) FROM {tool_name}_growth)
        GROUP BY GROUPING SETS (
            (date, orgs.practice_code, orgs.practice_name, orgs.pcn_code, orgs.pcn_name, orgs.icb_code, orgs.icb_name, orgs.region_code, orgs.region_name, subpara),
            (date, orgs.pcn_code, orgs.pcn_name, subpara),
            (date, orgs.icb_code, orgs.icb_name, subpara),
            (date, orgs.region_code, orgs.region_name, subpara),
            (date, subpara)
        )
    )
    SELECT
        date,
        org_level,
        practice_code,
        practice_name,
        pcn_code,
        pcn_name,
        icb_code,
        icb_name,
        region_code,
        region_name,
        subpara,
        spend_last_12m,
        spend_prev_12m,
        items_last_12m,
        items_prev_12m,
        CASE WHEN spend_prev_12m IS NULL OR spend_prev_12m = 0 THEN 'new' ELSE 'existing' END AS spend_type,
        CASE WHEN spend_prev_12m IS NULL OR spend_prev_12m = 0 THEN NULL
            ELSE (spend_last_12m - spend_prev_12m) / spend_prev_12m
        END AS cost_growth,
        CASE WHEN items_prev_12m IS NULL OR items_prev_12m = 0 THEN NULL
            ELSE (items_last_12m - items_prev_12m) / items_prev_12m
        END AS item_growth,
        DENSE_RANK() OVER (
            PARTITION BY practice_code,
            CASE WHEN spend_prev_12m IS NULL OR spend_prev_12m = 0 THEN 'new' ELSE 'existing' END
            ORDER BY spend_last_12m DESC
        ) AS spend_rank,
        DENSE_RANK() OVER (
            PARTITION BY practice_code,
            CASE WHEN items_prev_12m IS NULL OR items_prev_12m = 0 THEN 'new' ELSE 'existing' END
            ORDER BY items_last_12m DESC
        ) AS items_rank
    FROM grouped
    """
)
st.write(growth) 