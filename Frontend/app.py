import time
import sys
from pathlib import Path

import streamlit as st
import pyodbc
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.sql_executor import run_query
from Backend.text_to_sql import generate_sql

st.set_page_config(page_title="IntellectSQL AI", layout="wide")
st.title("IntellectSQL AI")
st.write("Ask a question about your database in plain English.")

with st.sidebar:
    st.header("How to use")
    st.markdown(
        "1. Enter a question to generate SQL.\n"
        "2. Review or edit the query.\n"
        "3. Run it to view the results."
    )
    st.info("Only read-only SELECT queries are allowed.")

with st.form("question_form"):
    question = st.text_area(
        "Your question",
        placeholder="e.g., Show incident file numbers and dates",
        height=100,
    )
    submitted = st.form_submit_button("Generate SQL", type="primary")

if submitted:
    st.session_state.pop("generated_sql", None)
    st.session_state.pop("query_results", None)

    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        try:
            with st.spinner("Generating SQL..."):
                sql = generate_sql(question)
            st.session_state["generated_sql"] = sql
            st.session_state["sql_editor"] = sql
        except (ValueError, RuntimeError) as error:
            st.error(str(error))

if st.session_state.get("generated_sql"):
    st.subheader("Review SQL")
    sql = st.text_area("Edit query before running:", key="sql_editor", height=200)

    if st.button("Run SELECT query", type="primary"):
        start = time.perf_counter()
        try:
            with st.spinner("Running query..."):
                results = run_query(sql)
            st.session_state["query_results"] = results
            st.session_state["query_time"] = time.perf_counter() - start
        except (ValueError, RuntimeError, pyodbc.Error, pd.errors.DatabaseError) as e:
            st.session_state.pop("query_results", None)
            st.error(str(e))

    results = st.session_state.get("query_results")
    if results is not None:
        st.subheader("Results")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(results))
        c2.metric("Columns", len(results.columns))
        c3.metric("Query time", f"{st.session_state.get('query_time', 0):.2f} sec")

        st.dataframe(results, use_container_width=True)
        st.download_button(
            "Download CSV",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name="query_results.csv",
            mime="text/csv",
        )
