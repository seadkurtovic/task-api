# Task API CI/CD Learning Project

This project is a minimal FastAPI service designed to practice CI/CD promotion flows across three long-lived branches:

- `dev` -> development
- `test` -> staging
- `main` -> production

## Business Use Case

This branch models a lightweight customer support operations API for a SaaS team.
Agents can create and prioritize incoming tickets, assign owners, update status,
and managers can view a dashboard of open/overdue work.

## API

- `GET /health` -> `{"status":"ok"}`
- `GET /tasks`
  - Optional filters: `status`, `priority`, `customer_name`, `assignee`, `overdue_only`
  - Returns `{"tasks":[...]}`
- `POST /tasks`
  - Example body:
    - `{"title":"Refund request","customer_name":"Acme","priority":"urgent","assignee":"Mia","due_date":"2026-04-10"}`
  - Returns created task including `id`, `status`, and `done`
- `PATCH /tasks/{task_id}`
  - Example body: `{"status":"in_progress","assignee":"Noah"}`
  - Updates status/priority/assignee and keeps `done` in sync with status
- `GET /dashboard`
  - Returns manager metrics:
    - total tasks
    - count by status
    - count by priority
    - overdue open task count
- `GET /dashboard/sla`
  - Optional filter: `priority`
  - Returns open-task SLA view:
    - total open tasks
    - tasks due today
    - overdue task count
    - ordered breach list with `days_overdue`

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
If your current GitHub plan/repo type does not support advanced environment protection
rules (for example, wait timers on private Free repositories), the script falls back
to creating basic environments and continues.
