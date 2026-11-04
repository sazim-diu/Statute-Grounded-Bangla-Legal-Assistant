"""Central configuration. All secrets come from environment variables (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "lexbangla.db"))
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
LLM_API_KEY = os.getenv("LLM_API_KEY")

# --- Retrieval (FR-2) ---
# Multilingual model with Bangla support (SRS 2.3). Change it in .env to compare models.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
CHROMA_DIR = os.getenv(
    "CHROMA_DIR", str(PROJECT_ROOT / "backend" / "data" / "chroma_db_e5")
)
CHUNKS_FILE = os.getenv(
    "CHUNKS_FILE",
    str(PROJECT_ROOT / "backend" / "data" / "processed" / "labour_act_chunks.json"),
)
TOP_K_DEFAULT = int(os.getenv("TOP_K", "5"))  # SRS FR-2: default k = 5
