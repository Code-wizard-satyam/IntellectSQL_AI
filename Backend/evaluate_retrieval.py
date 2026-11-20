import json
import time
from pathlib import Path
from statistics import mean

from Backend.schema_retriever import retrieve_schema

REPORTS_DIR = Path(__file__).resolve().parent.parent / "Reports"
QUESTIONS_PATH = REPORTS_DIR / "retrieval_eval_questions.json"
RESULTS_PATH = REPORTS_DIR / "retrieval_eval_results.json"


def calc_metrics(retrieved: set, expected: set) -> tuple[float, float]:
    hits = retrieved & expected
    precision = len(hits) / len(retrieved) if retrieved else 0.0
    recall = len(hits) / len(expected) if expected else 0.0
    return precision, recall


def evaluate(top_k: int = 4) -> dict:
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    results = []

    for item in questions:
        start = time.perf_counter()
        retrieved = retrieve_schema(item["question"], top_k=top_k)
        latency_ms = (time.perf_counter() - start) * 1000

        retrieved_tables = [doc["id"] for doc in retrieved]
        t_prec, t_rec = calc_metrics(set(retrieved_tables), set(item["expected_tables"]))

        retrieved_cols = {
            f"{doc['id']}.{col}"
            for doc in retrieved
            for col in doc["metadata"].get("columns", [])
        }
        expected_cols = {
            f"{tbl}.{col}"
            for tbl, cols in item["expected_columns"].items()
            for col in cols
        }
        c_prec, c_rec = calc_metrics(retrieved_cols, expected_cols)

        results.append({
            "question": item["question"],
            "expected_tables": item["expected_tables"],
            "retrieved_tables": retrieved_tables,
            "expected_columns": item["expected_columns"],
            "retrieved_columns": sorted(retrieved_cols),
            "table_precision": t_prec,
            "table_recall": t_rec,
            "column_precision": c_prec,
            "column_recall": c_rec,
            "latency_ms": latency_ms,
            "retrieved_documents": retrieved,
        })

    summary = {
        "question_count": len(questions),
        "top_k": top_k,
        "mean_table_precision": mean(r["table_precision"] for r in results),
        "mean_table_recall": mean(r["table_recall"] for r in results),
        "mean_column_precision": mean(r["column_precision"] for r in results),
        "mean_column_recall": mean(r["column_recall"] for r in results),
        "mean_latency_ms": mean(r["latency_ms"] for r in results),
    }

    report = {"summary": summary, "results": results}
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate()["summary"], indent=2))
