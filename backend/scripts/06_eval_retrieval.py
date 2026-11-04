"""Measure retrieval quality (SRS FR-34, AIR-1): Hit@1/3/5 and MRR.

Put labelled questions in backend/data/eval/questions.json (see questions_template.json).
Each section number must be checked by a team member against the Act text.

Usage: python backend/scripts/06_eval_retrieval.py
Compare models: run it once per EMBEDDING_MODEL (rebuild the index in between).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import config  # noqa: E402
from backend.retrieval import service  # noqa: E402
from backend.retrieval.data_cleaning import normalise_section_number  # noqa: E402

QUESTIONS = Path(__file__).resolve().parents[1] / "data" / "eval" / "questions.json"


def main() -> None:
    if not QUESTIONS.exists():
        sys.exit(f"{QUESTIONS} not found. Copy questions_template.json to questions.json and fill it in.")
    items = [q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q.get("expected_sections")]
    if not items:
        sys.exit("No labelled questions found.")

    hits = {1: 0, 3: 0, 5: 0}
    rr_sum = 0.0
    misses = []
    for q in items:
        expected = {normalise_section_number(s) for s in q["expected_sections"]}
        out = service.search(q["question"], k=10, log=False)
        ranks = [r["rank"] for r in out["results"] if r["section_number"] in expected]
        first = min(ranks) if ranks else None
        for k in hits:
            if first is not None and first <= k:
                hits[k] += 1
        rr_sum += 1.0 / first if first else 0.0
        if first is None or first > 5:
            misses.append((q["question"], sorted(expected), [r["section_number"] for r in out["results"][:5]]))

    n = len(items)
    print(f"Model: {config.EMBEDDING_MODEL}   questions: {n}")
    for k in (1, 3, 5):
        print(f"Hit@{k}: {hits[k] / n:.2%}")
    print(f"MRR:    {rr_sum / n:.3f}   (SRS target: Hit@5 >= 75%)")
    if misses:
        print("\nNot in top 5:")
        for question, expected, got in misses:
            print(f"- {question}\n    expected {expected}, got {got}")


if __name__ == "__main__":
    main()
