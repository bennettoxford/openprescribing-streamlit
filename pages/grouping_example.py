import altair as alt
import streamlit as st
import pandas as pd

from db import duckdb_path, query

st.set_page_config(layout="wide")

st.title("Example: how to use `GROUPING SETS`")
