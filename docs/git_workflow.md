# Git workflow (team rules)

1. Set your own identity once (email must match your GitHub account):
   git config --global user.name "Your Name"
   git config --global user.email "your-github-email"
2. Never push to `main` directly. Work on a branch: `feature/<module>`.
3. Commit small and often, from your own account, only your own work.
4. Message style: `feat(auth): ...`, `feat(retrieval): ...`, `fix(...)`, `docs: ...`, `test: ...`
5. Open a Pull Request, a teammate reviews, then merge.
6. Never commit `.env`, API keys, or database files.
