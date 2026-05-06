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
