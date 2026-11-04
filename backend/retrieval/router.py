"""POST /search: semantic retrieval with exact citations (FR-2, FR-4)."""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import get_current_user
from backend.retrieval import service
from backend.retrieval.index import IndexMismatchError
from backend.retrieval.schemas import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, _: dict = Depends(get_current_user)):
    try:
        return service.search(
            body.question, k=body.k, act_id=body.act_id, session_id=body.session_id
        )
    except (service.IndexNotBuiltError, service.IndexStaleError, IndexMismatchError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
