"""Minimal task API used for CI/CD learning workflows."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Task API")


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)


class Task(BaseModel):
    id: int
    title: str
    done: bool = False


_tasks: list[Task] = []
_next_id = 1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> dict[str, list[Task]]:
    return {"tasks": _tasks}


@app.post("/tasks")
def create_task(payload: TaskCreate) -> Task:
    global _next_id
    task = Task(id=_next_id, title=payload.title, done=False)
    _tasks.append(task)
    _next_id += 1
    return task
