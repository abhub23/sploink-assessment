from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EventMetadata(BaseModel, extra="allow"):
    file: Optional[str] = None
    status: Optional[str] = "unknown"


class EventInput(BaseModel):
    session_id: str
    timestamp: int
    step: int
    action: str = Field(pattern="^(read_file|write_file|run_command|llm_call)$")
    input: str = ""
    output: str = ""
    metadata: Optional[EventMetadata] = None


class EventResponse(BaseModel):
    id: str
    session_id: str
    timestamp: int
    step: int
    action: str
    input: str
    output: str
    metadata: dict


class SessionSummary(BaseModel):
    session_id: str
    status: str = "healthy"
    total_steps: int = 0
    success_count: int = 0
    failure_count: int = 0
    action_distribution: dict = {}
    detected_issues: list = []
    last_updated: Optional[datetime] = None


class DetectionResult(BaseModel):
    session_id: str
    issues: list = []
    status: str = "healthy"
    metrics: dict = {}
