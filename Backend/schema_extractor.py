from Backend.connection import get_connection

SCHEMA_SQL = """
SELECT
    c.TABLE_SCHEMA,
    c.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    pkc.COLUMN_NAME AS PRIMARY_KEY,
    OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS FK_SCHEMA,
    OBJECT_NAME(fk.referenced_object_id) AS FK_TABLE,
    COL_NAME(fk.referenced_object_id, fkc.referenced_column_id) AS FK_COLUMN
FROM INFORMATION_SCHEMA.COLUMNS AS c
LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS pk
    ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA
    AND pk.TABLE_NAME = c.TABLE_NAME
    AND pk.CONSTRAINT_TYPE = 'PRIMARY KEY'
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS pkc
    ON pkc.CONSTRAINT_SCHEMA = pk.CONSTRAINT_SCHEMA
    AND pkc.CONSTRAINT_NAME = pk.CONSTRAINT_NAME
    AND pkc.TABLE_SCHEMA = c.TABLE_SCHEMA
    AND pkc.TABLE_NAME = c.TABLE_NAME
    AND pkc.COLUMN_NAME = c.COLUMN_NAME
LEFT JOIN sys.foreign_key_columns AS fkc
    ON fkc.parent_object_id = OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + '.' + QUOTENAME(c.TABLE_NAME))
    AND COL_NAME(fkc.parent_object_id, fkc.parent_column_id) = c.COLUMN_NAME
LEFT JOIN sys.foreign_keys AS fk
    ON fk.object_id = fkc.constraint_object_id
ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION;
"""


def get_schema_metadata():
    conn = get_connection()
    try:
        rows = conn.execute(SCHEMA_SQL).fetchall()
    finally:
        conn.close()

    tables = {}
    for row in rows:
        key = (row.TABLE_SCHEMA, row.TABLE_NAME)
        if key not in tables:
            tables[key] = {
                "schema": row.TABLE_SCHEMA,
                "table": row.TABLE_NAME,
                "columns": {},
            }

        cols = tables[key]["columns"]
        if row.COLUMN_NAME not in cols:
            cols[row.COLUMN_NAME] = {
                "name": row.COLUMN_NAME,
                "data_type": row.DATA_TYPE,
                "primary_key": False,
                "foreign_keys": [],
            }

        if row.PRIMARY_KEY:
            cols[row.COLUMN_NAME]["primary_key"] = True

        if row.FK_TABLE:
            fk = {
                "schema": row.FK_SCHEMA,
                "table": row.FK_TABLE,
                "column": row.FK_COLUMN,
            }
            if fk not in cols[row.COLUMN_NAME]["foreign_keys"]:
                cols[row.COLUMN_NAME]["foreign_keys"].append(fk)

    result = []
    for table in tables.values():
        table["columns"] = list(table["columns"].values())
        result.append(table)
    return result


def get_schema_text():
    lines = []
    for table in get_schema_metadata():
        lines.append(f"\nTable: {table['schema']}.{table['table']}")
        for col in table["columns"]:
            text = f"  - {col['name']} ({col['data_type']})"
            if col["primary_key"]:
                text += " [PK]"
            for fk in col["foreign_keys"]:
                text += f" -> FK({fk['schema']}.{fk['table']}.{fk['column']})"
            lines.append(text)
    return "\n".join(lines).lstrip()
