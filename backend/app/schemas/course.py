import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class CourseCreate(BaseModel):
    title: str
    description: str
    level: str = "beginner"
    language: str = "python"
    thumbnail_url: Optional[str] = None


class CourseResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    level: str
    language: str
    thumbnail_url: Optional[str]
    total_duration: int
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int = 0


class LessonCreate(BaseModel):
    title: str
    content: str
    lesson_type: str = "text"
    order_index: int = 0
    duration: int = 0
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None


class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    progress: float
    completed_lessons: List[str]
    is_completed: bool
    enrolled_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CertificateResponse(BaseModel):
    id: uuid.UUID
    certificate_number: str
    course_id: uuid.UUID
    issued_at: datetime
    pdf_path: Optional[str]

    class Config:
        from_attributes = True
