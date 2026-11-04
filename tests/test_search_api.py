from backend.retrieval import service
from backend.retrieval.index import MemoryIndex
from backend.retrieval.indexer import build_index
from backend.retrieval.loader import load_chunks
from tests.helpers import HashEmbedder
from tests.test_retrieval_service import CHUNKS

USER = {"username": "searcher_1", "password": "Strong#Pass1"}


def auth_headers(client):
    client.post("/auth/register", json=USER)
    token = client.post("/auth/login", json=USER).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def setup_engine():
    load_chunks(CHUNKS, "2026-11-04", rebuild=True)
    emb, idx = HashEmbedder(), MemoryIndex()
    build_index(emb, idx)
    service.set_engine(service.SearchEngine(emb, idx))


def test_search_requires_login(client):
    assert client.post("/search", json={"question": "মজুরি পরিশোধ"}).status_code == 401


def test_search_success_shape(client):
    setup_engine()
    r = client.post("/search", json={"question": "শ্রমিকের মজুরি পরিশোধ"}, headers=auth_headers(client))
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["section_number"] == "১"
    assert body["snapshot_date"] == "2026-11-04"
    assert body["disclaimer"] and body["amendment_notice"]
    assert {"act_name", "section_number", "text", "source_url", "score"} <= body["results"][0].keys()
    service.set_engine(None)


def test_search_validation(client):
    headers = auth_headers(client)
    assert client.post("/search", json={"question": "ab"}, headers=headers).status_code == 422
    assert client.post("/search", json={"question": "x" * 501}, headers=headers).status_code == 422
    assert client.post("/search", json={"question": "মজুরি", "k": 50}, headers=headers).status_code == 422


def test_search_returns_503_when_index_is_empty(client):
    service.set_engine(service.SearchEngine(HashEmbedder(), MemoryIndex()))
    r = client.post("/search", json={"question": "মজুরি পরিশোধ"}, headers=auth_headers(client))
    assert r.status_code == 503
    service.set_engine(None)
