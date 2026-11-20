import unittest

from Backend.schema_retriever import retrieve_schema
from Backend.sql_executor import validate_select
from Backend.text_to_sql import clean_sql


class TestSQLAgent(unittest.TestCase):
    def test_retrieve_schema(self):
        results = retrieve_schema("Find incident file numbers and dates", top_k=4)
        tables = [r["id"] for r in results]
        self.assertIn("dbo.IncidentLog_TBL", tables)

        with self.assertRaises(ValueError):
            retrieve_schema("   ")

    def test_validate_select(self):
        query = "SELECT TOP 5 * FROM dbo.IncidentLog_TBL"
        self.assertEqual(validate_select(query), query)

        with self.assertRaises(ValueError):
            validate_select("UPDATE dbo.IncidentLog_TBL SET inlFileNo_TXT = 'x'")

        with self.assertRaises(ValueError):
            validate_select("SELECT 1; SELECT 2")

        cte = "WITH Recent AS (SELECT TOP 5 * FROM dbo.IncidentLog_TBL) SELECT * FROM Recent"
        self.assertEqual(validate_select(cte), cte)

    def test_clean_sql(self):
        raw = "```sql\nSELECT * FROM dbo.Building_TBL\n```"
        self.assertEqual(clean_sql(raw), "SELECT * FROM dbo.Building_TBL")


if __name__ == "__main__":
    unittest.main()
