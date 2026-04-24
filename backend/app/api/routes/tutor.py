import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.models.learning import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.learning import ChatMessageRequest, ChatMessageResponse
from app.services.ai_service import chat_with_tutor
from app.core.security import get_current_user

router = APIRouter()


@router.post("/chat", response_model=ChatMessageResponse)
async def chat(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with the AI tutor."""
    # Get or create session
    session = None
    if request.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        await db.flush()

    # Get conversation history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))

    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]
    messages.append({"role": "user", "content": request.content})

    # Get AI response
    response_lang = request.response_language or current_user.response_language
    ai_response = await chat_with_tutor(
        messages=messages,
        code_context=request.code_context,
        language=request.language,
        response_language=response_lang,
    )

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.content,
    )
    db.add(user_msg)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return ChatMessageResponse(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        session_id=session.id,
        created_at=assistant_msg.created_at,
    )


@router.get("/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    return {"message": "Session deleted"}
