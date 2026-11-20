import json
import re
from pathlib import Path

METADATA_PATH = Path(__file__).resolve().parent.parent / "Schema" / "schema_metadata.json"

STOP_WORDS = {
    "a", "an", "and", "are", "by", "find", "for", "from", "get", "give",
    "how", "in", "is", "list", "many", "me", "of", "on", "show", "the",
    "to", "what", "which", "who", "with", "tbl", "txt", "dtm", "frk",
    "prk", "bln", "mem", "int", "id",
}
WORD_FORMS = {"people": "person", "no": "number"}


def tokenize(text: str) -> set[str]:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[a-z0-9]+", text.lower())
    tokens = set()

    for word in words:
        if word in WORD_FORMS:
            word = WORD_FORMS[word]
        elif word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 3:
            word = word[:-1]

        if word not in STOP_WORDS and not word.isdigit():
            tokens.add(word)
    return tokens


def format_table(table: dict) -> dict:
    table_id = f"{table['schema']}.{table['table']}"
    col_lines = []

    for col in table["columns"]:
        line = f"{col['name']} ({col['data_type']})"
        if col.get("primary_key"):
            line += " [PK]"
        for fk in col.get("foreign_keys", []):
            line += f" [FK -> {fk['schema']}.{fk['table']}.{fk['column']}]"
        col_lines.append(line)

    return {
        "id": table_id,
        "page_content": f"Table: {table_id}\nColumns: " + "; ".join(col_lines),
        "metadata": {
            "schema": table["schema"],
            "table": table["table"],
            "columns": [col["name"] for col in table["columns"]],
        },
    }


def retrieve_schema(query: str, top_k: int = 6, metadata_path: Path = METADATA_PATH) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("Question must not be empty.")

    query_tokens = tokenize(query)
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    ranked = []

    for table in metadata.get("tables", []):
        table_tokens = tokenize(table["table"])
        col_tokens = {tok for col in table["columns"] for tok in tokenize(col["name"])}

        score = 6 * len(query_tokens & table_tokens) + 2 * len(query_tokens & col_tokens)
        if score > 0:
            doc = format_table(table)
            doc["score"] = score
            ranked.append(doc)

    ranked.sort(key=lambda d: (-d["score"], d["id"]))
    return ranked[:top_k]
