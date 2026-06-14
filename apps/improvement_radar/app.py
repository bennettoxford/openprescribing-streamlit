import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import json
from io import StringIO
from db import query
from charts import plot_improvement_chart
from utils import sidebar_logo, global_styles, sidebar_nav

# This makes Streamlit use whole page -t his has to be the first line of code, and inserts the OP logo into the browser
st.set_page_config(layout="wide", page_icon="content/OpenPrescribing.svg")

# --- Constants ---
tool_name = Path(__file__).parent.name
app_path = Path(__file__).parent
MEASURE_LIST_CACHE = app_path / 'csvs' / 'measure_list.csv'

# --- Functions ---

# grab measure list from GitHub - if that doesn't work, default to cached version
@st.cache_data(ttl=60*60*24)
def get_measure_list():
    try:
        res = fetch_url(
            'https://api.github.com/repos/ebmdatalab/openprescribing/contents/'
            'openprescribing/measures/definitions'
        )
        df_files = pd.read_json(StringIO(res.text))
        json_files = df_files[df_files['name'].str.contains('.json')]

        json_df = pd.DataFrame()
        for row in json_files.itertuples():
            data = json.loads(fetch_url(row.download_url).text)
            norm_df = pd.json_normalize(data, max_level=1)
            norm_df['table_id'] = 'ccg_data_' + row.name.replace('.json', '')
            json_df = pd.concat([json_df, norm_df], axis=0, ignore_index=True)

        tags_df = json_df.explode('tags')
        core_df = tags_df[['table_id', 'name', 'tags', 'radar_exclude', 'is_percentage', 'y_label']].copy()

        measure_list = core_df[
            (core_df['tags'].str.contains('core') | core_df['tags'].str.contains('lowpriority')) &
            (core_df['radar_exclude'] != 'True')
        ]

        measure_list.to_csv(MEASURE_LIST_CACHE, index=False)
        return measure_list

    except Exception as e:
        if MEASURE_LIST_CACHE.exists():
            st.warning("Could not fetch latest measure list from GitHub, using cached version.")
            return pd.read_csv(MEASURE_LIST_CACHE)
        raise e

# get SICBL names from cached csv
@st.cache_data
def load_sicbl_df():
    return pd.read_csv(app_path / 'csvs' / 'sicbl.csv')[['code', 'name']].rename(columns={'name': 'sicbl_name'})


def find_improving_orgs(df, start_threshold=0.8, end_threshold=0.5, min_numerator=50, top_x=5):
    """
    Identifies organisations that have shown substantial improvement across a measure.
    
    For each measure/org combination, finds any 6-month window where the org was in the
    top prescribers (percentile > start_threshold), followed by any later 6-month window
    where they had improved to below end_threshold. Returns the top_x orgs per measure
    ranked by largest percentile drop.

    Args:
        df: DataFrame with columns measure, code, month, numerator, calc_value, percentile
        start_threshold: org must average above this percentile in a 6-month window to qualify (default 0.8 = top 20%)
        end_threshold: org must average below this percentile in a later 6-month window (default 0.5 = bottom 50%)
        min_numerator: minimum mean numerator (prescription items) to exclude low-volume orgs (default 50)
        top_x: number of top orgs to return per measure (default 5)
    """

    # pre-filter to reduce data

    # drop measures where with insufficient items (<50 in numerator)
    mean_numerator = df.groupby(['measure', 'code'])['numerator'].transform('mean')
    df = df[mean_numerator > min_numerator]

    # drop orgs that never reach the start threshold
    max_percentile = df.groupby(['measure', 'code'])['percentile'].transform('max')
    df = df[max_percentile > start_threshold]

    # drop orgs that never reach the end threshold
    min_percentile = df.groupby(['measure', 'code'])['percentile'].transform('min')
    df = df[min_percentile < end_threshold]

    results = []
    for (measure, code), group in df.groupby(['measure', 'code']):
        group = group.sort_values('month').reset_index(drop=True)

        if group['numerator'].mean() <= min_numerator:
            continue

        percentiles = group['percentile'].values
        rates = group['calc_value'].values
        months = group['month'].values
        n = len(percentiles)

        # slide a 6-month window forward looking for a high-prescribing period
        for i in range(n - 6):
            start_mean = percentiles[i:i+6].mean()
            if start_mean > start_threshold:
                # found a high window at i — now look for a later low window
                for j in range(i + 6, n - 5):
                    end_mean = percentiles[j:j+6].mean()
                    if end_mean < end_threshold:
                        # confirm rate also dropped by at least 5%
                        rate_change = (rates[i:i+6].mean() - rates[j:j+6].mean()) / rates[i:i+6].mean()
                        if rate_change >= 0.05:
                            results.append({
                                'measure': measure,
                                'code': code,
                                'start_percentile': start_mean,
                                'end_percentile': end_mean,
                                'high_period_start': months[i],
                                'change_detected': months[i+6],
                                'low_period_start': months[j],
                            })
                            break  # take the first qualifying end window
                else:
                    continue
                break  # take the first qualifying start window

    results_df = pd.DataFrame(results)
    if results_df.empty:
        return results_df

    # rank by largest percentile drop and return top_x per measure
    return (results_df
            .sort_values('end_percentile', ascending=False)
            .groupby('measure')
            .head(top_x))

# --- App ---

# inserts logo into sidebar
sidebar_logo()

# applies CSS for navigation bar
global_styles()

# welcome banner
st.info(
"""
##### Hello!  This is a **very** early prototype of a new version of our Sub-ICB level Improvement Radar.
Please let us know what you think, and what you'd like to see.  Email us at [bennett@phc.ox.ac.uk](mailto:bennett@phc.ox.ac.uk)
"""
)

# Methodology explainer
with st.expander(
    "Click here to read our methodology", icon=":material/quick_reference:", expanded=True
):
    with open(Path(__file__).parent / "content/methodology.md") as f:
        st.markdown(f.read())

# Sidebar 

# header
with st.sidebar:
    st.markdown("### SICBL Improvement Radar")

# gives navigation to other tools
sidebar_nav()

# get measures list
measures = get_measure_list()
measure_ids = tuple(measures['table_id'].astype(str).unique())

ir_raw = query(
    f"""
    SELECT
        measure,
        pct_id AS code,
        month,
        numerator,
        denominator,
        calc_value,
        percentile
    FROM {tool_name}_ir_sicbl
    WHERE measure IN {measure_ids}
    """
)
ir = find_improving_orgs(ir_raw)

ir = ir.merge(
    measures[['table_id', 'name', 'is_percentage', 'y_label']].drop_duplicates('table_id'),
    left_on='measure',
    right_on='table_id',
    how='left'
)







sicbl = load_sicbl_df()

selected_name = st.selectbox(
    "Select measure",
    options=ir[['measure', 'name']].drop_duplicates().sort_values('name')['name'].tolist(),
)

selected_table_id = ir[ir['name'] == selected_name]['measure'].values[0]

top_orgs = ir[ir['measure'] == selected_table_id]['code'].tolist()

deciles_df = (
    ir_raw[ir_raw['measure'] == selected_table_id]
    .groupby('month')['calc_value']
    .quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    .reset_index()
    .rename(columns={'level_1': 'percentile', 'calc_value': 'rate'})
)

org_df = ir_raw[
    (ir_raw['measure'] == selected_table_id) &
    (ir_raw['code'].isin(top_orgs))
].merge(sicbl, left_on='code', right_on='code', how='left')

org_df = org_df[org_df['sicbl_name'].notna()]
plot_improvement_chart(deciles_df, org_df)

table_df = (
    ir[ir['measure'] == selected_table_id][['code', 'start_percentile', 'change_detected']]
    .merge(sicbl, on='code', how='left')
    .drop(columns='code')
    .rename(columns={
        'sicbl_name': 'Organisation',
        'start_percentile': 'High percentile',
        'change_detected': 'Change detected',
    })
)

table_df = table_df[table_df['Organisation'].notna()]

for col in ['High percentile']:
    table_df[col] = (table_df[col] * 100).round(1).astype(str) + '%'

for col in ['Change detected']:
    table_df[col] = pd.to_datetime(table_df[col]).dt.strftime('%b %Y')

cols = ['Organisation'] + [c for c in table_df.columns if c != 'Organisation']
table_df = table_df[cols]

st.dataframe(table_df, hide_index=True)