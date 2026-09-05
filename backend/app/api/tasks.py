"""Task execution API endpoints per Section 7 of master plan."""

import os
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.agent.graph import AgentWorkflowEngine
from app.agent.state import TaskState
from app.schemas.events import AgentEvent
from app.schemas.tasks import (
    Artifact,
    Citation,
    TaskCreateRequest,
    TaskResultResponse,
    TaskStatusResponse,
)

tasks_router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Store active and completed tasks in-memory and on disk
_tasks: Dict[str, TaskState] = {}
_tasks_lock = threading.Lock()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = BASE_DIR / "data" / "artifacts"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Will be initialized with retrieve_fn from main
workflow_engine: Optional[AgentWorkflowEngine] = None


def init_workflow_engine(retrieve_fn):
    global workflow_engine
    workflow_engine = AgentWorkflowEngine(artifacts_dir=ARTIFACTS_DIR, retrieve_fn=retrieve_fn)


def _run_task_async(state: TaskState):
    if workflow_engine:
        workflow_engine.execute(state)


@tasks_router.post("", response_model=TaskStatusResponse)
async def create_task(
    task: str = Form("Analyze inspection report against refinery SOP-402 and generate engineering approval note."),
    mode: str = Form("document_agent"),  # document_agent, knowledge_assistant, coding_agent
    files: List[UploadFile] = File(None),
):
    """Start an agentic task workflow."""
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    saved_files = []

    if files:
        for f in files:
            if f.filename:
                content = await f.read()
                save_path = UPLOAD_DIR / f"{task_id}_{f.filename}"
                save_path.write_bytes(content)
                saved_files.append({
                    "filename": f.filename,
                    "path": str(save_path),
                    "mime_type": f.content_type or "application/octet-stream",
                    "size": len(content),
                })

    state = TaskState(
        task_id=task_id,
        user_request=task,
        files=saved_files,
        task_type=mode,
        status="pending",
        current_step="queued",
    )

    with _tasks_lock:
        _tasks[task_id] = state

    # Execute workflow in worker thread
    thread = threading.Thread(target=_run_task_async, args=(state,), daemon=True)
    thread.start()

    return TaskStatusResponse(
        task_id=task_id,
        status="running",
        current_step="task_initialization",
        task_type=mode,
        progress_percentage=10,
    )


@tasks_router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    with _tasks_lock:
        state = _tasks.get(task_id)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found.")

    progress = 100 if state.status == "completed" else (15 if state.status == "running" else 0)
    return TaskStatusResponse(
        task_id=state.task_id,
        status=state.status,
        current_step=state.current_step,
        task_type=state.task_type,
        selected_model=state.selected_model,
        progress_percentage=progress,
        error=state.error,
    )


@tasks_router.get("/{task_id}/events")
def get_task_events(task_id: str):
    with _tasks_lock:
        state = _tasks.get(task_id)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {
        "task_id": task_id,
        "events": [event.model_dump() for event in state.events],
        "total_events": len(state.events),
        "status": state.status,
    }


@tasks_router.get("/{task_id}/result", response_model=TaskResultResponse)
def get_task_result(task_id: str):
    with _tasks_lock:
        state = _tasks.get(task_id)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found.")

    if state.status == "running" or state.status == "pending":
        raise HTTPException(status_code=202, detail="Task is still executing.")

    return TaskResultResponse(
        task_id=state.task_id,
        task_type=state.task_type,
        status=state.status,
        answer=state.answer,
        artifacts=state.artifacts,
        citations=state.citations,
        model_used=state.selected_model,
        security_verified=True,
    )


@tasks_router.get("/{task_id}/artifacts/{artifact_name}")
def download_artifact(task_id: str, artifact_name: str):
    with _tasks_lock:
        state = _tasks.get(task_id)

    if not state:
        raise HTTPException(status_code=404, detail="Task not found.")

    target_path = ARTIFACTS_DIR / artifact_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Artifact file not found.")

    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if artifact_name.endswith(".docx") else "application/octet-stream"
    return FileResponse(
        path=str(target_path),
        filename=artifact_name,
        media_type=media_type,
    )
