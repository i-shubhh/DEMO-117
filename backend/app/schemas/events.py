"""Event schemas for the Sovereign AI Workbench according to Section 7."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def get_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentEvent(BaseModel):
    task_id: str
    timestamp: str = Field(default_factory=get_utc_timestamp)
    type: str  # task_started, router_decision, ocr_started, ocr_completed, rag_search, rag_result, model_started, tool_called, tool_completed, artifact_created, security_check, task_completed, task_failed
    step: str
    status: str = "completed"  # started, completed, failed, pending
    model: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
