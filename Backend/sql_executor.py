import pandas as pd
import sqlparse
from sqlparse.tokens import Comment, Keyword

from Backend.connection import get_connection

FORBIDDEN_KEYWORDS = {
    "ALTER", "CREATE", "DELETE", "DROP", "EXEC", "EXECUTE",
    "GRANT", "INSERT", "INTO", "MERGE", "REVOKE", "TRUNCATE", "UPDATE",
}


def validate_select(sql: str) -> str:
    if not sql or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        raise ValueError("Only a single SELECT statement is allowed.")

    statement = statements[0]
    first_keyword = next(
        (
            token.value.upper()
            for token in statement.flatten()
            if token.ttype in Keyword
        ),
        None,
    )
    if first_keyword not in {"SELECT", "WITH"}:
        raise ValueError("Only a single read-only SELECT statement is allowed.")

    for token in statement.flatten():
        if token.ttype in Comment:
            continue
        if token.ttype in Keyword and token.value.upper() in FORBIDDEN_KEYWORDS:
            raise ValueError(f"Keyword '{token.value.upper()}' is not allowed.")

    return sql.strip()


def run_query(sql: str) -> pd.DataFrame:
    safe_sql = validate_select(sql)
    conn = get_connection()
    try:
        return pd.read_sql_query(safe_sql, conn)
    finally:
        conn.close()
