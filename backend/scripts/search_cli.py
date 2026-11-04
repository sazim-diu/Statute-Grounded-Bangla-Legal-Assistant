"""Try a search from the terminal (no login, nothing is logged).

Usage: python backend/scripts/search_cli.py "মজুরি না দিলে কী করা যায়?"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.retrieval import service  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = service.search(" ".join(sys.argv[1:]), log=False)
    print(f"Snapshot: {out['snapshot_date']}   best score: {out['best_score']}\n")
    for r in out["results"]:
        print(f"[{r['rank']}] {r['act_name']} - ধারা {r['section_number']}: {r['title']}  (score {r['score']})")
        print(f"    {r['chapter']}")
        print("    " + r["text"][:200].replace("\n", " ") + " ...\n")


if __name__ == "__main__":
    main()
