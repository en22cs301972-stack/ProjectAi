import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Any


class CodeExecuteRequest(BaseModel):
    code: str
    language: str  # python, java, sql
    stdin: Optional[str] = None
    problem_id: Optional[uuid.UUID] = None


class TestCase(BaseModel):
    input: str
    expected_output: str
    description: Optional[str] = None


class CodeExecuteResponse(BaseModel):
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    memory_used: Optional[int] = None
    test_results: Optional[List[dict]] = None
    ai_feedback: Optional[str] = None


class AIDebugRequest(BaseModel):
    code: str
    language: str
    error_message: str
    response_language: Optional[str] = "en"


class AIDebugResponse(BaseModel):
    explanation: str
    line_fixes: List[dict]
    optimized_code: Optional[str] = None
    suggestions: List[str]


class ProblemCreate(BaseModel):
    title: str
    description: str
    difficulty: str = "easy"
    language: str = "python"
    starter_code: str
    solution_code: str
    test_cases: List[TestCase] = []
    hints: List[str] = []
    tags: List[str] = []


class ProblemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    difficulty: str
    language: str
    starter_code: str
    hints: List[str]
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    content: str
    session_id: Optional[uuid.UUID] = None
    code_context: Optional[str] = None
    language: Optional[str] = None
    response_language: Optional[str] = "en"


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    session_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
