import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from Backend.schema_retriever import retrieve_schema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SYSTEM_PROMPT = """You write read-only Microsoft SQL Server queries.
Use only the supplied schema. Return one SQL SELECT statement and no markdown.
Never generate INSERT, UPDATE, DELETE, or DDL statements.
If the schema does not support the request, say so instead of inventing columns."""


def clean_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def generate_sql(question: str, top_k: int = 4, model: str = None) -> str:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    tables = retrieve_schema(question, top_k=top_k)
    if not tables:
        raise ValueError("No matching tables found in schema.")

    model = model or os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    schema = "\n\n".join(t["page_content"] for t in tables)

    payload = json.dumps({
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question:\n{question.strip()}\n\nSchema:\n{schema}"},
        ],
    }).encode("utf-8")

    req = Request(
        f"{base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as res:
            data = json.loads(res.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Ollama returned HTTP {error.code}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not connect to Ollama at {base_url}") from error

    sql = data.get("message", {}).get("content", "").strip()
    if not sql:
        raise RuntimeError("Ollama returned an empty response.")

    return clean_sql(sql)
