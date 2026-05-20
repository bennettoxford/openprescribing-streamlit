import altair as alt
import streamlit as st

from db import duckdb_path, query

st.title("OpenPrescribing Streamlit")

st.caption(f"Database: {duckdb_path}")

prescribing_count = query("SELECT COUNT(*) FROM prescribing").iat[0, 0]
items_by_chapter = query(
    """
    SELECT
        prescribing.date,
        bnf_code.code AS chapter_code,
        bnf_code.name AS chapter,
        SUM(prescribing.items) AS items
    FROM prescribing
    JOIN bnf_code
        ON bnf_code.code = SUBSTR(prescribing.bnf_code, 1, 2)
        AND bnf_code.level = 1
    GROUP BY prescribing.date, bnf_code.code, bnf_code.name
    ORDER BY prescribing.date, bnf_code.code
    """
)

chapter_order = (
    items_by_chapter.sort_values("chapter_code")["chapter"].drop_duplicates().tolist()
)

st.metric("Prescribing rows", f"{prescribing_count:,}")

st.subheader("Items over time by BNF chapter")
chart = (
    alt.Chart(items_by_chapter)
    .mark_bar()
    .properties(height=500)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("items:Q", title="Items"),
        color=alt.Color(
            "chapter:N",
            sort=chapter_order,
            legend=alt.Legend(columns=2, orient="bottom", title=None),
        ),
        order=alt.Order("chapter_code:N"),
    )
)
st.altair_chart(chart, use_container_width=True)

oral_antibiotics = query(
    """
    WITH oral_form_route_ids AS (
        SELECT list(cd) AS ids
        FROM ont_form_route
        WHERE descr LIKE '%.oral'
    ),
    oral_bnf_codes AS (
        SELECT DISTINCT medications.bnf_code
        FROM medications, oral_form_route_ids
        WHERE medications.bnf_code IS NOT NULL
          AND list_has_any(medications.form_route_ids, oral_form_route_ids.ids)
    )
    SELECT prescribing.date, SUM(prescribing.items) AS items
    FROM prescribing
    JOIN oral_bnf_codes USING (bnf_code)
    WHERE prescribing.bnf_code LIKE '0502%'
    GROUP BY prescribing.date
    ORDER BY prescribing.date
    """
)

st.subheader("Oral antibiotics, items over time")
st.line_chart(oral_antibiotics, x="date", y="items")
