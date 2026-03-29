# Task API CI/CD Learning Project

This project is a minimal FastAPI service designed to practice CI/CD promotion flows across three long-lived branches:

- `dev` -> development
- `test` -> staging
- `main` -> production

## API

- `GET /health` -> `{"status":"ok"}`
- `GET /tasks` -> `{"tasks":[...]}`
- `POST /tasks` with `{"title":"string"}` -> `{"id":1,"title":"string","done":false}`

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
ruff check .
```

## GitHub Actions

- CI workflow: `.github/workflows/ci.yml`
  - Runs on push and pull requests to `dev`, `test`, and `main`
  - Required checks: `lint` and `test`
- Simulated CD workflow: `.github/workflows/cd-simulated.yml`
  - Runs on push to `dev`, `test`, and `main`
  - Uses environments:
    - `dev` -> `development`
    - `test` -> `staging`
    - `main` -> `production`
  - Uploads deployment metadata artifact with branch, commit SHA, and UTC timestamp

## Branch Strategy

After the first commit:

```bash
git branch -m main
git branch dev
git branch test
```

## Configure GitHub Protections and Environments

After pushing `dev`, `test`, and `main` to GitHub, run:

```bash
./scripts/configure_github_repo.sh owner/repo
```

The script configures:

- Environments:
  - `development` wait timer `0`
  - `staging` wait timer `60`
  - `production` wait timer `180`
- Branch protection on `dev`, `test`, `main`:
  - Require pull requests
  - Require status checks `lint` and `test`
  - Block force pushes and deletions
  - Require conversation resolution

Note: you must be authenticated with `gh auth login` and have admin rights on the repository.
