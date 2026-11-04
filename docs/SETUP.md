# Setup and run (LexBangla)

Run everything from the repository root, with the virtual environment active.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put a random SECRET_KEY (32+ characters) in .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # use this value for SECRET_KEY

# 1. database + statute sections (use the real date the Act was scraped)
python backend/scripts/04_load_chunks_to_sqlite.py --snapshot-date YYYY-MM-DD

# 2. embeddings + ChromaDB (first run downloads the model, needs internet)
python backend/scripts/05_build_embedding_index.py

# 3. try it in the terminal
python backend/scripts/search_cli.py "মালিক বেতন না দিলে শ্রমিক কী করতে পারেন?"

# 4. run the app (two terminals)
uvicorn backend.main:app --reload
streamlit run frontend/app.py

# admin user (password is typed at the prompt)
python backend/scripts/create_admin.py

# tests
pytest
```

Re-running step 1 on a filled database needs `--rebuild`. After step 1 with `--rebuild`,
run step 2 again so the index matches the database.

Measure retrieval: copy `backend/data/eval/questions_template.json` to `questions.json`,
fill in questions and checked section numbers, then `python backend/scripts/06_eval_retrieval.py`.
