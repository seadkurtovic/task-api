from datetime import date, timedelta

from fastapi.testclient import TestClient

import app.main as task_api


client = TestClient(task_api.app)


def setup_function() -> None:
    task_api._tasks.clear()
    task_api._next_id = 1


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_tasks() -> None:
    create_response = client.post(
        "/tasks",
        json={
            "title": "Investigate failed login",
            "customer_name": "Contoso",
            "priority": "high",
            "assignee": "Mia",
            "due_date": "2999-12-31",
        },
    )

    assert create_response.status_code == 200
    assert create_response.json() == {
        "id": 1,
        "title": "Investigate failed login",
        "customer_name": "Contoso",
        "description": None,
        "priority": "high",
        "status": "todo",
        "assignee": "Mia",
        "due_date": "2999-12-31",
        "done": False,
    }

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert list_response.json() == {
        "tasks": [
            {
                "id": 1,
                "title": "Investigate failed login",
                "customer_name": "Contoso",
                "description": None,
                "priority": "high",
                "status": "todo",
                "assignee": "Mia",
                "due_date": "2999-12-31",
                "done": False,
            }
        ]
    }


def test_filter_tasks_by_priority_and_status() -> None:
    client.post(
        "/tasks",
        json={"title": "Refund request", "customer_name": "Acme", "priority": "urgent"},
    )
    client.post(
        "/tasks",
        json={"title": "Export issue", "customer_name": "Acme", "priority": "medium"},
    )
    client.patch("/tasks/2", json={"status": "in_progress", "assignee": "Noah"})

    urgent_response = client.get("/tasks?priority=urgent")
    in_progress_response = client.get("/tasks?status=in_progress")
    customer_response = client.get("/tasks?customer_name=Acme")

    assert urgent_response.status_code == 200
    assert len(urgent_response.json()["tasks"]) == 1
    assert urgent_response.json()["tasks"][0]["title"] == "Refund request"

    assert in_progress_response.status_code == 200
    assert len(in_progress_response.json()["tasks"]) == 1
    assert in_progress_response.json()["tasks"][0]["assignee"] == "Noah"

    assert customer_response.status_code == 200
    assert len(customer_response.json()["tasks"]) == 2


def test_filter_tasks_overdue_only() -> None:
    client.post(
        "/tasks",
        json={"title": "Past due task", "customer_name": "Contoso", "due_date": "2000-01-01"},
    )
    client.post(
        "/tasks",
        json={"title": "Future task", "customer_name": "Contoso", "due_date": "2999-01-01"},
    )
    client.patch("/tasks/1", json={"status": "done"})

    overdue_response = client.get("/tasks?overdue_only=true")

    assert overdue_response.status_code == 200
    assert overdue_response.json() == {"tasks": []}

    client.patch("/tasks/1", json={"status": "todo"})

    overdue_response = client.get("/tasks?overdue_only=true")
    assert overdue_response.status_code == 200
    assert len(overdue_response.json()["tasks"]) == 1
    assert overdue_response.json()["tasks"][0]["title"] == "Past due task"


def test_update_task_status_marks_done() -> None:
    client.post("/tasks", json={"title": "Upgrade plan", "customer_name": "Northwind"})
    update_response = client.patch("/tasks/1", json={"status": "done", "assignee": "Ava"})

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "done"
    assert update_response.json()["done"] is True
    assert update_response.json()["assignee"] == "Ava"


def test_update_missing_task_returns_404() -> None:
    response = client.patch("/tasks/999", json={"status": "blocked"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Task 999 not found"}


def test_dashboard_reports_totals_and_overdue_open() -> None:
    client.post(
        "/tasks",
        json={"title": "Escalated bug", "customer_name": "Acme", "priority": "urgent", "due_date": "2000-01-01"},
    )
    client.post(
        "/tasks",
        json={"title": "Billing question", "customer_name": "Acme", "priority": "medium", "due_date": "2000-01-01"},
    )
    client.post(
        "/tasks",
        json={"title": "Feature onboarding", "customer_name": "Northwind", "priority": "high", "due_date": "2999-01-01"},
    )
    client.patch("/tasks/2", json={"status": "done"})
    client.patch("/tasks/3", json={"status": "in_progress"})

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.json() == {
        "total": 3,
        "by_status": {"todo": 1, "in_progress": 1, "blocked": 0, "done": 1},
        "by_priority": {"low": 0, "medium": 1, "high": 1, "urgent": 1},
        "overdue_open": 1,
    }


def test_sla_report_counts_priority_and_breaches() -> None:
    today = date.today()
    one_day_ago = (today - timedelta(days=1)).isoformat()
    three_days_ago = (today - timedelta(days=3)).isoformat()
    due_today = today.isoformat()

    client.post(
        "/tasks",
        json={"title": "Escalated outage", "customer_name": "Acme", "priority": "urgent", "due_date": three_days_ago},
    )
    client.post(
        "/tasks",
        json={"title": "Billing follow-up", "customer_name": "Contoso", "priority": "medium", "due_date": one_day_ago},
    )
    client.post(
        "/tasks",
        json={"title": "Onboarding workshop", "customer_name": "Northwind", "priority": "high", "due_date": due_today},
    )
    client.post(
        "/tasks",
        json={"title": "Legacy cleanup", "customer_name": "Acme", "priority": "low", "due_date": one_day_ago},
    )
    client.patch("/tasks/4", json={"status": "done"})

    full_report = client.get("/dashboard/sla")
    urgent_report = client.get("/dashboard/sla?priority=urgent")

    assert full_report.status_code == 200
    assert full_report.json()["total_open"] == 3
    assert full_report.json()["due_today"] == 1
    assert full_report.json()["overdue"] == 2
    assert [item["title"] for item in full_report.json()["breaches"]] == [
        "Escalated outage",
        "Billing follow-up",
    ]
    assert full_report.json()["breaches"][0]["days_overdue"] == 3
    assert full_report.json()["breaches"][1]["days_overdue"] == 1

    assert urgent_report.status_code == 200
    assert urgent_report.json() == {
        "total_open": 1,
        "due_today": 0,
        "overdue": 1,
        "breaches": [
            {
                "id": 1,
                "title": "Escalated outage",
                "customer_name": "Acme",
                "priority": "urgent",
                "status": "todo",
                "assignee": None,
                "due_date": three_days_ago,
                "days_overdue": 3,
            }
        ],
    }
