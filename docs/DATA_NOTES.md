# Notes on the statute data (for the data/retrieval owners)

`backend/scripts/04_load_chunks_to_sqlite.py` cleans `labour_act_chunks.json` while loading and
writes `backend/data/processed/data_quality_report.json`. The original JSON is not modified.
Problems found in `02_legal_chunker.py` output, and what the loader does about them:

| Problem | Effect | Loader action |
|---|---|---|
| Each section body ends with the next section's heading | shown "original text" contained a foreign heading | heading removed |
| Last section of each chapter got the next chapter's name | wrong chapter in citation | chapter corrected |
| ~105 chapters are really section text (e.g. `১৭৬৷ এই অধ্যায়ের ...`) | garbage in citation | previous valid chapter used |
| 43 titles are only a footnote number (e.g. `92`) | wrong title | real heading recovered from the end of the previous section |
| Section `৭` appears twice (a sub-clause `৭।` taken as a section) | duplicate, wrong text | second copy kept in DB but not indexed |
| Repealed sections 184 and 253-262 have text written by the script, not copied from the Act | invented legal text | not indexed; neutral note stored |
| Sections 168, 176, 286 are missing (their lines were taken as chapter headings) | those sections cannot be found | listed in the report; **fix `CHAPTER_PATTERN` in `02_legal_chunker.py`** |
| `legal_status` / amendment note: `f"ধারা {n}" in fn` also matches `ধারা 184` for n = 1 | wrong "Amended" labels | stored but not shown to users; fix with a boundary check, e.g. `re.search(rf"ধারা\s*{n}(?![০-৯ক-হ])", fn)` |
| A few sections still end with a stray footnote number (e.g. `306`) | small noise at the end of text | not handled |

The best long-term fix is in the chunker itself; then the loader's cleaning steps become no-ops.
