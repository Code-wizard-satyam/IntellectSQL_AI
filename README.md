# IntellectSQL AI

IntellectSQL AI is a local text-to-SQL application for Microsoft SQL Server. It retrieves relevant schema metadata, sends the question and schema to an Ollama model, validates the response as a read-only SQL query, and displays the results in Streamlit.

## Architecture

1. SQL Server schema extraction
2. Table and column metadata indexing
3. Lexical schema retrieval
4. Ollama SQL generation
5. SQL validation and read-only execution
6. Streamlit results and CSV export

## Features

- Extracts tables, columns, primary keys, and foreign keys from SQL Server.
- Retrieves relevant schema documents before SQL generation.
- Generates one SQL SELECT statement with Ollama.
- Validates and executes only read-only queries.
- Provides a Streamlit interface with editable SQL and CSV export.
- Includes a reproducible retrieval evaluation report.

## Setup

1. Create the virtual environment and install dependencies:

   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Install Microsoft ODBC Driver 18 for SQL Server.

3. Copy `.env.example` to `.env` and enter the SQL Server and Ollama settings.

4. Install and run Ollama, then confirm the configured model is available:

   ```powershell
   ollama pull qwen3.5:2b
   ```

5. Index the live database schema:

   ```powershell
   python -m Backend.schema_indexer
   ```

   Enter `y` when prompted to refresh metadata from SQL Server.

6. Start the application:

   ```powershell
   streamlit run Frontend/app.py
   ```

## Evaluation

Run retrieval metrics against `Reports/retrieval_eval_questions.json`:

```powershell
python -m Backend.evaluate_retrieval
```

The report is written to `Reports/retrieval_eval_results.json`.

## Validation

```powershell
python -m unittest discover -s tests -v
python -m compileall -q Backend Frontend
```
