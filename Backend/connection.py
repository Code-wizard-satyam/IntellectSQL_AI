import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise ValueError(f"Missing required environment variable: {name}")
    return val


def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={get_env('SQL_SERVER')};"
        f"DATABASE={get_env('SQL_DATABASE')};"
        f"UID={get_env('SQL_USERNAME')};"
        f"PWD={get_env('SQL_PASSWORD')};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


if __name__ == "__main__":
    with get_connection() as conn:
        row = conn.execute("SELECT DB_NAME(), SYSTEM_USER").fetchone()
        print(row)
