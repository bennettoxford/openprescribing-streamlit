import altair as alt
import streamlit as st
import pandas as pd

from db import duckdb_path, query

st.set_page_config(layout="wide")

st.title("Example: how to use `GROUPING SETS`")

st.markdown("""
We've been running two similar separate queries at different `GROUP BY` levels to get information for the topx prescribing tool.

i.e.
```
    SELECT
        med.vtm_id AS vtm,
        vtm.nm AS name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    from prescribing AS rx
    inner join
    medications as med
    ON
    rx.snomed_code = med.id
    inner join
    vtm AS vtm
    ON
    med.vtm_id = vtm.vtmid
    INNER JOIN _selected_practices AS s
      ON rx.practice_code = s.practice_code
    WHERE
    date between '2025-01-01' and '2025-12-01'
    GROUP BY vtm.nm, med.vtm_id


    SELECT
        med.vtm_id AS vtm,
        med.name AS name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    from prescribing AS rx
    inner join
    medications as med
    ON
    rx.snomed_code = med.id
    INNER JOIN _selected_practices AS s
      ON rx.practice_code = s.practice_code
    WHERE
    date between '2025-01-01' and '2025-12-01'
    GROUP BY med.vtm_id, med.name

```

However, we should be able to reduce query time by using `GROUPING SETS` which can group at multiple levels, giving a `NULL` at the lower level.
We can then separate them using Python to create different data sets.
```
    SELECT
        med.vtm_id AS vtm,
        vtm.nm AS name,
        med.name AS name,
        sum(items) as items,
        sum(actual_cost/100) as actual_cost
    from prescribing AS rx
    inner join
    medications as med
    ON
    rx.snomed_code = med.id
    INNER JOIN _selected_practices AS s
      ON rx.practice_code = s.practice_code
    WHERE
    date between '2025-01-01' and '2025-12-01'
    GROUP BY GROUPING SETS (
    (vtm.nm,med.vtm_id, med.name),
    (vtm.nm,med.vtm_id)
```
"""
)

df_topx = query(
    """
    SELECT
        med.vtm_id AS vtm,
        vtm.nm AS vtm_name,
        med.name AS name,
        SUM(rx.items) AS items,
        SUM(rx.actual_cost / 100) AS actual_cost
    FROM prescribing AS rx
    INNER JOIN medications AS med
        ON rx.snomed_code = med.id
    INNER JOIN vtm AS vtm
        ON med.vtm_id = vtm.vtmid
    WHERE rx.date BETWEEN '2025-01-01' AND '2025-12-01'
    GROUP BY GROUPING SETS (
        (vtm.nm, med.vtm_id, med.name),
        (vtm.nm, med.vtm_id)
        )
"""
)

df_topx_example = df_topx[df_topx["vtm"] == 776991000]

st.markdown(
    """
    An example of this is omprazole (VTM `776991000`)
    """
)

st.dataframe(df_topx_example)

st.markdown(
    """
    This has got lots of lines at the VMP/AMP level, and then one single line with a NULL in the presentation name, showing the sum for all.

    We can then separate them out using:

    `df_summary = df_topx_example[df_topx_example["name"].isna()].drop(columns="name")` 

    `df_detail = df_topx_example[df_topx_example["name"].notna()]`  
    """
)

df_summary = df_topx_example[df_topx_example["name"].isna()].drop(columns="name")
df_detail = df_topx_example[df_topx_example["name"].notna()]

st.markdown("Summary table")
st.dataframe(df_summary)

st.markdown("Detail table")
st.dataframe(df_detail)