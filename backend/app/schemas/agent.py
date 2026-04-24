import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: str = "custom"
    config: Dict[str, Any] = {}
    tools_enabled: List[str] = []
    api_keys: Optional[Dict[str, str]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools_enabled: Optional[List[str]] = None
    api_keys: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    agent_type: str
    status: str
    is_active: bool
    config: Dict[str, Any]
    tools_enabled: List[str]
    last_run_at: Optional[datetime]
    total_runs: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentLogResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    level: str
    message: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRunRequest(BaseModel):
    task: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
