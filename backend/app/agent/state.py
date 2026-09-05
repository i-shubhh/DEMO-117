"""Minimal TaskState definition per Section 11 of master plan."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.schemas.events import AgentEvent
from app.schemas.tasks import Artifact, Citation


@dataclass
class TaskState:
    task_id: str
    user_request: str
    files: List[Dict[str, Any]] = field(default_factory=list)
    task_type: str = "document"  # visual_document, knowledge_reasoning, coding
    selected_model: str = "qwen2.5vl:3b"
    extracted_content: str = ""
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Artifact] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    events: List[AgentEvent] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    current_step: str = "initialized"
    answer: str = ""
    error: Optional[str] = None

    def add_event(self, event_type: str, step: str, status: str = "completed", details: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> AgentEvent:
        event = AgentEvent(
            task_id=self.task_id,
            type=event_type,
            step=step,
            status=status,
            model=model or self.selected_model,
            details=details or {},
        )
        self.events.append(event)
        self.current_step = step
        return event
