import sys
import time
import sys
from pathlib import Path

import streamlit as st
import pyodbc
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.schema_extractor import get_schema_metadata
from Backend.sql_executor import run_query
from Backend.text_to_sql import generate_sql


def show_sql_assistant():
    with st.form("question_form"):
        question = st.text_area(
            "Your question",
            placeholder="Show incident file numbers and dates",
            height=100,
        )
        submitted = st.form_submit_button("Generate SQL", type="primary")

    if submitted:
        st.session_state.pop("generated_sql", None)
        st.session_state.pop("query_results", None)
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                with st.spinner("Generating SQL..."):
                    sql = generate_sql(question)
                st.session_state["generated_sql"] = sql
                st.session_state["sql_editor"] = sql
            except (ValueError, RuntimeError) as error:
                st.error(str(error))

    if not st.session_state.get("generated_sql"):
        return

    st.subheader("Review SQL")
    sql = st.text_area("Edit the query before running it:", key="sql_editor", height=200)

    if st.button("Run SELECT query", type="primary"):
        started = time.perf_counter()
        try:
            with st.spinner("Running query..."):
                results = run_query(sql)
            st.session_state["query_results"] = results
            st.session_state["query_time"] = time.perf_counter() - started
        except (ValueError, RuntimeError, pyodbc.Error, pd.errors.DatabaseError) as error:
            st.session_state.pop("query_results", None)
            st.error(str(error))

    results = st.session_state.get("query_results")
    if results is not None:
        st.subheader("Results")
        rows, columns, duration = st.columns(3)
        rows.metric("Rows", len(results))
        columns.metric("Columns", len(results.columns))
        duration.metric("Query time", f"{st.session_state['query_time']:.2f} sec")
        st.dataframe(results, use_container_width=True)
        st.download_button(
            "Download CSV",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name="query_results.csv",
            mime="text/csv",
        )


def show_database_schema():
    st.write("Fetch the current tables, columns, primary keys, and foreign keys from SQL Server.")

    if st.button("Fetch schema", type="primary"):
        try:
            with st.spinner("Reading schema from SQL Server..."):
                st.session_state["database_schema"] = get_schema_metadata()
        except (ValueError, pyodbc.Error) as error:
            st.error(str(error))

    tables = st.session_state.get("database_schema")
    if tables is None:
        return

    st.caption(f"{len(tables)} tables")
    search = st.text_input("Find a table", placeholder="Type part of a table name")
    matching_tables = {
        f"{table['schema']}.{table['table']}": table
        for table in tables
        if search.casefold() in f"{table['schema']}.{table['table']}".casefold()
    }

    if not matching_tables:
        st.info("No tables match that search.")
        return

    selected_name = st.selectbox("Table", list(matching_tables))
    columns = [
        {
            "Column": column["name"],
            "Type": column["data_type"],
            "Primary key": "Yes" if column["primary_key"] else "",
            "Foreign key": ", ".join(
                f"{key['schema']}.{key['table']}.{key['column']}"
                for key in column["foreign_keys"]
            ),
        }
        for column in matching_tables[selected_name]["columns"]
    ]
    st.dataframe(pd.DataFrame(columns), hide_index=True, use_container_width=True)


st.set_page_config(page_title="IntellectSQL AI", layout="wide")
st.title("IntellectSQL AI")

section = st.radio(
    "Section",
    ["Ask a question", "Database schema"],
    horizontal=True,
    label_visibility="collapsed",
)

if section == "Database schema":
    st.subheader("Database schema")
    show_database_schema()
else:
    st.write("Ask a question about your database in plain English.")
    st.info("Only read-only SELECT queries can be run.")
    show_sql_assistant()