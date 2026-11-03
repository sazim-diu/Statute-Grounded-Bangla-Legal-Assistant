# LexBangla - Statute-Grounded Bangla Legal Assistant
SE331 capstone (Batch 42, Section B1). Bangla-first legal information tool grounded in the text of Bangladeshi Acts. Provides legal information only, not legal advice.

## Setup
```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in real values
python -m backend.db.database   # create SQLite tables
uvicorn backend.main:app --reload
```

## Run
```
uvicorn backend.main:app --reload          # API at http://127.0.0.1:8000/docs
streamlit run frontend/app.py              # UI
python scripts/create_admin.py             # create an admin (password typed at prompt)
pytest                                     # run tests
```

## Auth endpoints
| Method | Path | Access |
|---|---|---|
| POST | /auth/register | public |
| POST | /auth/login | public, returns JWT |
| GET | /auth/me | logged-in user |
| GET | /auth/users | admin only |

## Structure
- `backend/` FastAPI app: `auth/`, `retrieval/`, `generation/`, `feedback/`, `db/`
- `frontend/` Streamlit UI
- `data/` statute data (`raw/` collected text, `sections/` cleaned JSON)
- `scripts/` data loading and index building
- `docs/` team notes

## Team and ownership
| Member | Module |
|---|---|
| TBD | TBD |
