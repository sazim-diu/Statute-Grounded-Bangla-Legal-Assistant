"""Load labour_act_chunks.json into SQLite (act, snapshot, section tables).

Usage:
  python backend/scripts/04_load_chunks_to_sqlite.py --snapshot-date 2026-11-04
  python backend/scripts/04_load_chunks_to_sqlite.py --snapshot-date 2026-11-04 --rebuild

--snapshot-date is the day the Act text was scraped from bdlaws.minlaw.gov.bd
(SRS FR-30 shows this date to the user). It is required on purpose: do not guess it.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import config  # noqa: E402
from backend.retrieval.loader import SectionsAlreadyLoadedError, load_chunks_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--snapshot-date", required=True, help="YYYY-MM-DD, date the Act was scraped")
    parser.add_argument("--chunks", default=config.CHUNKS_FILE, help="path to the chunks JSON")
    parser.add_argument("--rebuild", action="store_true", help="replace sections already loaded")
    args = parser.parse_args()

    try:
        report = load_chunks_file(args.chunks, args.snapshot_date, rebuild=args.rebuild)
    except SectionsAlreadyLoadedError as exc:
        sys.exit(str(exc))

    out = Path(args.chunks).parent / "data_quality_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Loaded {report['total_records']} records "
          f"({report['indexed_records']} searchable, {report['not_indexed_records']} not indexed).")
    print("Fixes / flags applied:")
    for name, count in report["flag_counts"].items():
        print(f"  {name}: {count}")
    print("Sections missing from the source parse:",
          ", ".join(report["section_numbers_missing_from_source_parse"]) or "none")
    print(f"Full report: {out}")


if __name__ == "__main__":
    main()
