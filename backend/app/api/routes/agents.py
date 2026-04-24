import uuid
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict

from app.database import get_db
from app.models.agent import Agent, AgentLog, AgentStatus
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentLogResponse, AgentRunRequest
from app.services.mcp_service import run_agent_task, MCP_TOOLS
from app.core.security import get_current_user, encrypt_data, decrypt_data

router = APIRouter()

# In-memory store for running agent tasks
running_agents: Dict[str, asyncio.Task] = {}


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all agents for the current user."""
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent."""
    # Encrypt API keys
    encrypted_keys = None
    if agent_data.api_keys:
        encrypted_keys = encrypt_data(json.dumps(agent_data.api_keys))

    agent = Agent(
        user_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        agent_type=agent_data.agent_type,
        config=agent_data.config,
        tools_enabled=agent_data.tools_enabled,
        encrypted_api_keys=encrypted_keys,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    agent_update: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent_update.name is not None:
        agent.name = agent_update.name
    if agent_update.description is not None:
        agent.description = agent_update.description
    if agent_update.config is not None:
        agent.config = agent_update.config
    if agent_update.tools_enabled is not None:
        agent.tools_enabled = agent_update.tools_enabled
    if agent_update.is_active is not None:
        agent.is_active = agent_update.is_active
    if agent_update.api_keys is not None:
        agent.encrypted_api_keys = encrypt_data(json.dumps(agent_update.api_keys))

    await db.flush()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Stop if running
    agent_key = str(agent_id)
    if agent_key in running_agents:
        running_agents[agent_key].cancel()
        del running_agents[agent_key]

    await db.delete(agent)
    return {"message": "Agent deleted"}


@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: uuid.UUID,
    run_request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status == AgentStatus.running:
        raise HTTPException(status_code=400, detail="Agent is already running")

    # Update status
    agent.status = AgentStatus.running
    agent.last_run_at = datetime.utcnow()
    agent.total_runs += 1
    await db.flush()

    # Decrypt API keys
    api_keys = {}
    if agent.encrypted_api_keys:
        try:
            api_keys = json.loads(decrypt_data(agent.encrypted_api_keys))
        except Exception:
            pass

    # Run agent in background
    background_tasks.add_task(
        run_agent_background,
        agent_id=str(agent_id),
        config=agent.config,
        api_keys=api_keys,
        task=run_request.task or "Run default agent task",
        db=db,
    )

    return {"message": "Agent started", "agent_id": str(agent_id)}


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop a running agent."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Cancel running task
    agent_key = str(agent_id)
    if agent_key in running_agents:
        running_agents[agent_key].cancel()
        del running_agents[agent_key]

    agent.status = AgentStatus.stopped
    await db.flush()

    return {"message": "Agent stopped"}


@router.get("/{agent_id}/logs", response_model=List[AgentLogResponse])
async def get_agent_logs(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Get logs for an agent."""
    # Verify ownership
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    logs_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.agent_id == agent_id)
        .order_by(AgentLog.created_at.desc())
        .limit(limit)
    )
    return logs_result.scalars().all()


@router.get("/tools/available")
async def get_available_tools(current_user: User = Depends(get_current_user)):
    """Get all available MCP tools."""
    return {
        "tools": [
            {
                "name": name,
                "description": config["description"],
                "required_keys": config.get("required_keys", []),
            }
            for name, config in MCP_TOOLS.items()
        ]
    }


async def run_agent_background(
    agent_id: str,
    config: dict,
    api_keys: dict,
    task: str,
    db: AsyncSession,
):
    """Run agent task in the background."""
    try:
        result = await run_agent_task(
            agent_config=config,
            api_keys=api_keys,
            task=task,
        )

        # Log result
        log = AgentLog(
            agent_id=agent_id,
            level="info",
            message=f"Task completed: {result.get('result', 'Done')}",
            details=result,
        )
        db.add(log)

        # Update agent status
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if agent:
            agent.status = AgentStatus.idle

        await db.commit()

    except Exception as e:
        # Log error
        try:
            log = AgentLog(
                agent_id=agent_id,
                level="error",
                message=f"Task failed: {str(e)}",
            )
            db.add(log)

            agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
            agent = agent_result.scalar_one_or_none()
            if agent:
                agent.status = AgentStatus.error
                agent.last_error = str(e)

            await db.commit()
        except Exception:
            pass
