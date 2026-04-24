import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class AgentStatus(str, enum.Enum):
    idle = "idle"
    running = "running"
    stopped = "stopped"
    error = "error"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(100), default="custom")  # custom, gmail, market, crypto
    status: Mapped[str] = mapped_column(String(50), default=AgentStatus.idle)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Configuration
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    tools_enabled: Mapped[list] = mapped_column(JSON, default=list)  # MCP tools

    # Encrypted API keys storage
    encrypted_api_keys: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution stats
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_runs: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agents")
    logs = relationship("AgentLog", back_populates="agent", cascade="all, delete-orphan")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="info")  # info, warning, error
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="logs")
