import streamlit as st
import requests
import pandas as pd
import json
from io import StringIO
from db import query
import Path

tool_name = "improvement_radar"

app_path = Path(__file__).parent
MEASURE_LIST_CACHE = app_path / 'csvs' / 'measure_list.csv'

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


def find_improving_orgs(df, start_threshold=0.8, end_threshold=0.5, min_numerator=50, top_x=5):
    results = []
    for (measure, code), group in df.groupby(['measure', 'code']):
        group = group.sort_values('month').reset_index(drop=True)

        if group['numerator'].mean() <= min_numerator:
            continue

        percentiles = group['percentile'].values
        rates = group['calc_value'].values
        n = len(percentiles)

        for i in range(n - 6):
            start_mean = percentiles[i:i+6].mean()
            if start_mean > start_threshold:
                for j in range(i + 6, n - 5):
                    end_mean = percentiles[j:j+6].mean()
                    if end_mean < end_threshold:
                        rate_change = (rates[i:i+6].mean() - rates[j:j+6].mean()) / rates[i:i+6].mean()
                        if rate_change >= 0.05:
                            results.append({
                                'measure': measure,
                                'code': code,
                                'start_percentile': start_mean,
                                'end_percentile': end_mean,
                                'percentile_drop': start_mean - end_mean,
                            })
                            break
                else:
                    continue
                break

    results_df = pd.DataFrame(results)
    if results_df.empty:
        return results_df

    return (results_df
            .sort_values('percentile_drop', ascending=False)
            .groupby('measure')
            .head(top_x))


measures = get_measure_list()
measure_ids = tuple(measures['table_id'].unique())

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