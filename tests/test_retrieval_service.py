import pytest

from backend.db.database import get_connection, init_db
from backend.retrieval import service
from backend.retrieval.index import MemoryIndex
from backend.retrieval.indexer import build_index
from backend.retrieval.loader import SectionsAlreadyLoadedError, load_chunks
from tests.helpers import HashEmbedder

CHUNKS = [
    {"id": "sec_১", "section_number": "১", "section_title": "মজুরি পরিশোধ",
     "chapter": "দশম অধ্যায় (মজুরী ও উহার পরিশোধ)",
     "raw_body": "১। মালিক প্রতি মাসে শ্রমিকের মজুরি পরিশোধ করিবেন।\nছুটির পদ্ধতি",
     "legal_status": "সক্রিয় (Active)", "amendment_provenance": "x"},
    {"id": "sec_২", "section_number": "২", "section_title": "ছুটির পদ্ধতি",
     "chapter": "নবম অধ্যায় (কর্মঘণ্টা ও ছুটি)",
     "raw_body": "২। শ্রমিক ছুটির জন্য আবেদন করিতে পারিবেন।\nনিরাপত্তা",
     "legal_status": "সক্রিয় (Active)", "amendment_provenance": "x"},
    {"id": "sec_৩", "section_number": "৩", "section_title": "নিরাপত্তা",
     "chapter": "ষষ্ঠ অধ্যায় (নিরাপত্তা)",
     "raw_body": "৩। প্রতিষ্ঠানে অগ্নি নিরাপত্তা ব্যবস্থা থাকিতে হইবে।",
     "legal_status": "সক্রিয় (Active)", "amendment_provenance": "x"},
]


@pytest.fixture()
def engine():
    init_db()
    load_chunks(CHUNKS, "2026-11-04", rebuild=True)
    emb, idx = HashEmbedder(), MemoryIndex()
    build_index(emb, idx)
    eng = service.SearchEngine(emb, idx)
    service.set_engine(eng)
    yield eng
    service.set_engine(None)


def test_search_returns_most_similar_section_first(engine):
    out = service.search("শ্রমিকের মজুরি পরিশোধ", log=False)
    assert out["results"][0]["section_number"] == "১"
    assert out["results"][0]["score"] >= out["results"][1]["score"]


def test_citation_has_act_section_text_and_snapshot(engine):
    top = service.search("ছুটির জন্য আবেদন", log=False)["results"][0]
    assert top["act_name"] == "বাংলাদেশ শ্রম আইন, ২০০৬"
    assert top["section_number"] == "২"
    assert top["source_url"].startswith("https://bdlaws.minlaw.gov.bd")
    # text is exactly the stored statute text, with the next section's heading removed
    assert top["text"] == "২। শ্রমিক ছুটির জন্য আবেদন করিতে পারিবেন।"
    assert service.search("ছুটি", log=False)["snapshot_date"] == "2026-11-04"


def test_query_and_results_are_logged_without_personal_data(engine):
    out = service.search("অগ্নি নিরাপত্তা", session_id="abcdef1234567890")
    with get_connection() as conn:
        log = conn.execute("SELECT * FROM query_log WHERE log_id = ?", (out["query_id"],)).fetchone()
        rows = conn.execute(
            "SELECT * FROM retrieval_result WHERE log_id = ? ORDER BY rank", (out["query_id"],)
        ).fetchall()
    assert log["query_text"] == "অগ্নি নিরাপত্তা"
    assert log["session_id"] == "abcdef1234567890"
    assert log["retrieval_score"] == out["best_score"]
    assert [r["rank"] for r in rows] == [1, 2, 3]


def test_bad_session_id_is_replaced_with_random_value():
    sid = service.clean_session_id("x; DROP TABLE users")
    assert len(sid) == 32 and sid.isalnum()
    assert service.clean_session_id("short") != "short"


def test_k_is_limited(engine):
    assert len(service.search("মজুরি", k=2, log=False)["results"]) == 2
    assert len(service.search("মজুরি", k=99, log=False)["results"]) == 3  # only 3 sections exist


def test_act_filter_with_unknown_act_returns_nothing(engine):
    assert service.search("মজুরি", act_id=9999, log=False)["results"] == []


def test_empty_index_raises_clear_error():
    init_db()
    eng = service.SearchEngine(HashEmbedder(), MemoryIndex())
    with pytest.raises(service.IndexNotBuiltError):
        service.search("মজুরি", log=False, engine=eng)


def test_loading_twice_requires_rebuild(engine):
    with pytest.raises(SectionsAlreadyLoadedError):
        load_chunks(CHUNKS, "2026-11-04")
