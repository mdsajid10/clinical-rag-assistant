"""
Evaluation script for Clinical RAG Assistant.
Runs sample questions, compares responses using both keyword overlap
and semantic similarity, then saves results to evaluation/results.json.
"""

import json
import os
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402
from src.rag_chain import ask  # noqa: E402
from services.embedding_service import get_embeddings  # noqa: E402

QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "test_questions.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")


def keyword_score(answer: str, expected: list[str]) -> float:
    """Return the fraction of expected keywords found in *answer*."""
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected if kw.lower() in answer_lower)
    return hits / len(expected) if expected else 0.0


def semantic_score(answer: str, expected_answer: str) -> float:
    """Compute cosine similarity between answer and expected answer embeddings."""
    if not expected_answer:
        return 0.0

    embeddings = get_embeddings()
    vec_answer = embeddings.embed_query(answer)
    vec_expected = embeddings.embed_query(expected_answer)

    score = cosine_similarity([vec_answer], [vec_expected])[0][0]
    return float(score)


def run_evaluation() -> None:
    """Execute the evaluation pipeline with keyword + semantic scoring."""
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    total_keyword = 0.0
    total_semantic = 0.0

    for idx, item in enumerate(questions, 1):
        question = item["question"]
        expected_kw = item.get("expected_keywords", [])
        expected_ans = item.get("expected_answer", "")

        print(f"[{idx}/{len(questions)}] {question}")
        start = time.time()

        try:
            response = ask(question, session_id="eval")
            answer = response.get("answer", "")
            sources = response.get("sources", [])
        except Exception as exc:
            answer = f"ERROR: {exc}"
            sources = []

        elapsed = round(time.time() - start, 2)

        kw_score = keyword_score(answer, expected_kw)
        sem_score = semantic_score(answer, expected_ans) if expected_ans else 0.0
        total_keyword += kw_score
        total_semantic += sem_score

        results.append(
            {
                "question": question,
                "answer": answer,
                "sources": sources,
                "expected_keywords": expected_kw,
                "expected_answer": expected_ans,
                "keyword_score": round(kw_score, 3),
                "semantic_score": round(sem_score, 3),
                "response_time_sec": elapsed,
            }
        )
        print(f"   → keyword: {kw_score:.1%}  semantic: {sem_score:.1%}  time: {elapsed}s\n")

    n = len(questions) or 1
    summary = {
        "total_questions": len(questions),
        "average_keyword_score": round(total_keyword / n, 3),
        "average_semantic_score": round(total_semantic / n, 3),
        "results": results,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Evaluation complete.")
    print(f"  Avg keyword score:  {total_keyword / n:.1%}")
    print(f"  Avg semantic score: {total_semantic / n:.1%}")
    print(f"  Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    run_evaluation()
