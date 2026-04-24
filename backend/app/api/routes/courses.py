import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.models.course import Course, CourseModule, Lesson, Enrollment, Certificate
from app.models.user import User
from app.schemas.course import (
    CourseCreate, CourseResponse,
    ModuleCreate, LessonCreate,
    EnrollmentResponse, CertificateResponse,
)
from app.services.certificate_service import generate_certificate
from app.core.security import get_current_user
import secrets

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    level: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all published courses."""
    query = select(Course).where(Course.is_published == True)
    if level:
        query = query.where(Course.level == level)
    if language:
        query = query.where(Course.language == language)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=CourseResponse, status_code=201)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new course (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    course = Course(**course_data.model_dump())
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific course with its modules and lessons."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
async def enroll_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll in a course."""
    # Check course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check already enrolled
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
    )
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.get("/my/enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all enrollments for the current user."""
    result = await db.execute(
        select(Enrollment).where(Enrollment.user_id == current_user.id)
    )
    return result.scalars().all()


@router.put("/{course_id}/progress")
async def update_progress(
    course_id: uuid.UUID,
    lesson_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a lesson as completed and update progress."""
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    # Update completed lessons
    completed = list(enrollment.completed_lessons or [])
    if lesson_id not in completed:
        completed.append(lesson_id)
        enrollment.completed_lessons = completed

    # Calculate progress based on total lessons
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()

    # Count total lessons in course modules
    modules_result = await db.execute(
        select(CourseModule).where(CourseModule.course_id == course_id)
    )
    modules = modules_result.scalars().all()
    total_lessons = 0
    for module in modules:
        lessons_result = await db.execute(
            select(Lesson).where(Lesson.module_id == module.id)
        )
        total_lessons += len(lessons_result.scalars().all())

    if total_lessons > 0:
        enrollment.progress = (len(completed) / total_lessons) * 100

    # Check if completed
    if enrollment.progress >= 100 and not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.completed_at = datetime.utcnow()

        # Generate certificate in background
        background_tasks.add_task(
            issue_certificate,
            user_id=str(current_user.id),
            course_id=str(course_id),
            db=db,
        )

    await db.flush()
    return {
        "progress": enrollment.progress,
        "completed_lessons": enrollment.completed_lessons,
        "is_completed": enrollment.is_completed,
    }


async def issue_certificate(user_id: str, course_id: str, db: AsyncSession):
    """Issue a certificate for course completion."""
    from sqlalchemy import select as sa_select

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()

    if not user or not course:
        return

    # Check if certificate already exists
    cert_result = await db.execute(
        select(Certificate).where(
            Certificate.user_id == user_id,
            Certificate.course_id == course_id,
        )
    )
    if cert_result.scalar_one_or_none():
        return

    certificate_number = f"CERT-{secrets.token_hex(8).upper()}"

    pdf_path = generate_certificate(
        user_name=user.full_name or user.username,
        course_title=course.title,
        completion_date=datetime.utcnow(),
        certificate_number=certificate_number,
    )

    cert = Certificate(
        user_id=user_id,
        course_id=course_id,
        certificate_number=certificate_number,
        pdf_path=pdf_path,
    )
    db.add(cert)
    await db.commit()


@router.get("/certificates/my", response_model=List[CertificateResponse])
async def get_my_certificates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all certificates for the current user."""
    result = await db.execute(
        select(Certificate).where(Certificate.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/certificates/{certificate_id}/download")
async def download_certificate(
    certificate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a certificate PDF."""
    result = await db.execute(
        select(Certificate).where(
            Certificate.id == certificate_id,
            Certificate.user_id == current_user.id,
        )
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if not cert.pdf_path:
        raise HTTPException(status_code=404, detail="Certificate PDF not generated yet")

    return FileResponse(
        path=cert.pdf_path,
        media_type="application/pdf",
        filename=f"certificate_{cert.certificate_number}.pdf",
    )
