"""Task schemas for Sovereign AI Workbench."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    section: Optional[str] = None
    text: Optional[str] = None
    score: float = 0.0


class Artifact(BaseModel):
    name: str
    type: str  # docx, code, json, txt
    path: str
    download_url: str
    description: Optional[str] = None
    size_bytes: int = 0


class TaskCreateRequest(BaseModel):
    task: str = Field(..., description="Prompt or description of the task")
    mode: str = Field(default="document_agent", description="document_agent, knowledge_assistant, or coding_agent")
    options: Dict[str, Any] = Field(default_factory=dict)


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed
    current_step: str
    task_type: str
    selected_model: Optional[str] = None
    progress_percentage: int = 0
    error: Optional[str] = None


class TaskResultResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    answer: str
    artifacts: List[Artifact] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    model_used: Optional[str] = None
    security_verified: bool = True
