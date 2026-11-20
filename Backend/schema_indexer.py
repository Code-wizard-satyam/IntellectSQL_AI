import json
import time
from pathlib import Path

from Backend.schema_extractor import get_schema_metadata

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "Schema"
METADATA_PATH = SCHEMA_DIR / "schema_metadata.json"
DOCUMENTS_PATH = SCHEMA_DIR / "schema_documents.json"


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_documents(tables):
    documents = []
    for table in tables:
        table_id = f"{table['schema']}.{table['table']}"
        col_lines = []
        primary_keys = []
        foreign_keys = []

        for col in table["columns"]:
            desc = f"{col['name']} ({col['data_type']})"
            if col.get("primary_key"):
                desc += " [PK]"
                primary_keys.append(col["name"])

            for fk in col.get("foreign_keys", []):
                desc += f" [FK -> {fk['schema']}.{fk['table']}.{fk['column']}]"
                foreign_keys.append({
                    "column": col["name"],
                    "referenced_schema": fk["schema"],
                    "referenced_table": fk["table"],
                    "referenced_column": fk["column"],
                })

            col_lines.append(desc)

        documents.append({
            "id": table_id,
            "page_content": f"Table: {table_id}\nColumns: " + "; ".join(col_lines),
            "metadata": {
                "schema": table["schema"],
                "table": table["table"],
                "columns": [c["name"] for c in table["columns"]],
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
            },
        })
    return documents


def index_schema(refresh_schema=False):
    if refresh_schema:
        tables = get_schema_metadata()
        metadata = {
            "source": "SQL Server",
            "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "table_count": len(tables),
            "tables": tables,
        }
        save_json(METADATA_PATH, metadata)
    else:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

    tables = metadata.get("tables", [])
    if not tables:
        raise ValueError("No tables found in schema metadata.")

    save_json(DOCUMENTS_PATH, build_documents(tables))
    return len(tables)


if __name__ == "__main__":
    refresh = input("Refresh schema from SQL Server? [y/N]: ").strip().lower() == "y"
    print(f"Indexed {index_schema(refresh_schema=refresh)} tables")
