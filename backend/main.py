"""FastAPI entry point. Run with: uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.auth.router import router as auth_router
from backend.auth.security import get_secret
from backend.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_secret()  # fail fast if SECRET_KEY is not configured
    init_db()
    yield


app = FastAPI(title="LexBangla - Statute-Grounded Bangla Legal Assistant", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
