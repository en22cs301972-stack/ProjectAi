import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.models.learning import Problem, CodeSubmission, ChatSession, ChatMessage
from app.models.user import User
from app.schemas.learning import (
    CodeExecuteRequest, CodeExecuteResponse,
    AIDebugRequest, AIDebugResponse,
    ProblemCreate, ProblemResponse,
    ChatMessageRequest, ChatMessageResponse,
)
from app.services.code_execution import execute_code, run_test_cases
from app.services.ai_service import (
    explain_code_error, generate_code_feedback, chat_with_tutor, suggest_code_fix
)
from app.core.security import get_current_user

router = APIRouter()


@router.post("/execute", response_model=CodeExecuteResponse)
async def execute_code_endpoint(
    request: CodeExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute code and return results."""
    result = await execute_code(
        code=request.code,
        language=request.language,
        stdin=request.stdin,
    )

    # Run test cases if problem_id provided
    test_results = None
    if request.problem_id:
        problem_result = await db.execute(select(Problem).where(Problem.id == request.problem_id))
        problem = problem_result.scalar_one_or_none()
        if problem and problem.test_cases:
            test_results = await run_test_cases(request.code, request.language, problem.test_cases)
            all_passed = all(t["passed"] for t in test_results)
            result["status"] = "accepted" if all_passed else "wrong_answer"

    # Save submission
    submission = CodeSubmission(
        user_id=current_user.id,
        problem_id=request.problem_id,
        code=request.code,
        language=request.language,
        status=result["status"],
        output=result.get("output"),
        error=result.get("error"),
        execution_time=result.get("execution_time"),
        test_results=test_results,
    )
    db.add(submission)

    # Add AI feedback if there's an error
    ai_feedback = None
    if result.get("error") and result["status"] in ("runtime_error", "compile_error"):
        ai_feedback = await generate_code_feedback(
            code=request.code,
            language=request.language,
            response_language=current_user.response_language,
        )
        submission.ai_feedback = ai_feedback

    return CodeExecuteResponse(
        status=result["status"],
        output=result.get("output"),
        error=result.get("error"),
        execution_time=result.get("execution_time"),
        memory_used=result.get("memory_used"),
        test_results=test_results,
        ai_feedback=ai_feedback,
    )


@router.post("/debug", response_model=AIDebugResponse)
async def debug_code(
    request: AIDebugRequest,
    current_user: User = Depends(get_current_user),
):
    """Get AI-powered code debugging with line-by-line analysis."""
    response_lang = request.response_language or current_user.response_language
    result = await explain_code_error(
        code=request.code,
        language=request.language,
        error_message=request.error_message,
        response_language=response_lang,
    )
    return AIDebugResponse(**result)


@router.post("/suggest-fix")
async def get_code_fix(
    code: str,
    language: str,
    issue: str,
    current_user: User = Depends(get_current_user),
):
    """Get specific code fix suggestions."""
    return await suggest_code_fix(
        code=code,
        language=language,
        issue_description=issue,
        response_language=current_user.response_language,
    )


@router.get("/problems", response_model=List[ProblemResponse])
async def list_problems(
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all available coding problems."""
    query = select(Problem).where(Problem.is_published == True)
    if language:
        query = query.where(Problem.language == language)
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/problems/{problem_id}", response_model=ProblemResponse)
async def get_problem(
    problem_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific problem."""
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.post("/problems", response_model=ProblemResponse, status_code=201)
async def create_problem(
    problem_data: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new coding problem (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    problem = Problem(
        title=problem_data.title,
        description=problem_data.description,
        difficulty=problem_data.difficulty,
        language=problem_data.language,
        starter_code=problem_data.starter_code,
        solution_code=problem_data.solution_code,
        test_cases=[tc.dict() for tc in problem_data.test_cases],
        hints=problem_data.hints,
        tags=problem_data.tags,
    )
    db.add(problem)
    await db.flush()
    await db.refresh(problem)
    return problem


@router.get("/submissions")
async def get_my_submissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's code submissions."""
    result = await db.execute(
        select(CodeSubmission)
        .where(CodeSubmission.user_id == current_user.id)
        .order_by(CodeSubmission.submitted_at.desc())
        .limit(50)
    )
    submissions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "problem_id": str(s.problem_id) if s.problem_id else None,
            "language": s.language,
            "status": s.status,
            "execution_time": s.execution_time,
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in submissions
    ]
