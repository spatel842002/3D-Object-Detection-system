# Contributing

This is a personal portfolio project by Shriya Patel, but contributions,
issues, and forks are welcome.

## Local setup

See [docs/local-development.md](docs/local-development.md) for the full
one-command bootstrap. Short version:

```bash
python -m venv .venv
.venv/Scripts/activate   # or: source .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
pytest -m "not model_download"
```

## Before opening a PR

1. `ruff format src tests scripts`
2. `ruff check src tests scripts`
3. `mypy src`
4. `pytest -m "not model_download" --cov`
5. Update relevant docs under `docs/` if behavior or contracts changed.
6. Do not commit model weights, datasets, secrets, or `.env` files.

## Commit style

This repo uses [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...).

## Code of conduct

Participation in this project is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
