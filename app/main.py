"""Task API for CI/CD learning and support-ops workflow demos."""

from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high", "urgent"]
Status = Literal["todo", "in_progress", "blocked", "done"]

app = FastAPI(title="Task API")


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    customer_name: str = "internal"
    description: str | None = None
    priority: Priority = "medium"
    assignee: str | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = None


class Task(BaseModel):
    id: int
    title: str
    customer_name: str
    description: str | None = None
    priority: Priority = "medium"
    status: Status = "todo"
    assignee: str | None = None
    due_date: date | None = None
    done: bool = False


class DashboardMetrics(BaseModel):
    total: int
    by_status: dict[Status, int]
    by_priority: dict[Priority, int]
    overdue_open: int


class SlaBreach(BaseModel):
    id: int
    title: str
    customer_name: str
    priority: Priority
    status: Status
    assignee: str | None = None
    due_date: date
    days_overdue: int


class SlaReport(BaseModel):
    total_open: int
    due_today: int
    overdue: int
    breaches: list[SlaBreach]


_tasks: list[Task] = []
_next_id = 1
_priority_weight: dict[Priority, int] = {"low": 1, "medium": 2, "high": 3, "urgent": 4}


def _is_overdue(task: Task) -> bool:
    return task.due_date is not None and task.due_date < date.today() and task.status != "done"


def _find_task(task_id: int) -> Task:
    for task in _tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks(
    status: Status | None = Query(default=None),
    priority: Priority | None = Query(default=None),
    customer_name: str | None = Query(default=None),
    assignee: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
) -> dict[str, list[Task]]:
    filtered_tasks = _tasks

    if status is not None:
        filtered_tasks = [task for task in filtered_tasks if task.status == status]

    if priority is not None:
        filtered_tasks = [task for task in filtered_tasks if task.priority == priority]

    if customer_name is not None:
        filtered_tasks = [task for task in filtered_tasks if task.customer_name == customer_name]

    if assignee is not None:
        filtered_tasks = [task for task in filtered_tasks if task.assignee == assignee]

    if overdue_only:
        filtered_tasks = [task for task in filtered_tasks if _is_overdue(task)]

    return {"tasks": filtered_tasks}


@app.post("/tasks")
def create_task(payload: TaskCreate) -> Task:
    global _next_id
    task = Task(
        id=_next_id,
        title=payload.title,
        customer_name=payload.customer_name,
        description=payload.description,
        priority=payload.priority,
        assignee=payload.assignee,
        due_date=payload.due_date,
        status="todo",
        done=False,
    )
    _tasks.append(task)
    _next_id += 1
    return task


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    task = _find_task(task_id)

    if payload.status is not None:
        task.status = payload.status
        task.done = payload.status == "done"

    if payload.priority is not None:
        task.priority = payload.priority

    if payload.assignee is not None:
        task.assignee = payload.assignee

    return task


@app.get("/dashboard")
def dashboard() -> DashboardMetrics:
    by_status: dict[Status, int] = {"todo": 0, "in_progress": 0, "blocked": 0, "done": 0}
    by_priority: dict[Priority, int] = {"low": 0, "medium": 0, "high": 0, "urgent": 0}

    for task in _tasks:
        by_status[task.status] += 1
        by_priority[task.priority] += 1

    overdue_open = sum(1 for task in _tasks if _is_overdue(task))

    return DashboardMetrics(
        total=len(_tasks),
        by_status=by_status,
        by_priority=by_priority,
        overdue_open=overdue_open,
    )


@app.get("/dashboard/sla")
def sla_report(priority: Priority | None = Query(default=None)) -> SlaReport:
    today = date.today()
    open_tasks = [task for task in _tasks if task.status != "done"]

    if priority is not None:
        open_tasks = [task for task in open_tasks if task.priority == priority]

    due_today = sum(1 for task in open_tasks if task.due_date == today)
    overdue_tasks = [
        task for task in open_tasks if task.due_date is not None and task.due_date < today
    ]

    overdue_tasks.sort(
        key=lambda task: (_priority_weight[task.priority], (today - task.due_date).days),
        reverse=True,
    )

    breaches = [
        SlaBreach(
            id=task.id,
            title=task.title,
            customer_name=task.customer_name,
            priority=task.priority,
            status=task.status,
            assignee=task.assignee,
            due_date=task.due_date,
            days_overdue=(today - task.due_date).days,
        )
        for task in overdue_tasks
    ]

    return SlaReport(
        total_open=len(open_tasks),
        due_today=due_today,
        overdue=len(overdue_tasks),
        breaches=breaches,
    )
