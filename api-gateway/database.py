import asyncio
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, JSON, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import structlog

from config import settings

logger = structlog.get_logger()

# Database base
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON, default={})

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    channel = Column(String, index=True)  # email, chat, voice
    status = Column(String, default="active")  # active, resolved, escalated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON, default={})
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_conversation_channel_status', 'channel', 'status'),
        Index('idx_conversation_updated_at', 'updated_at'),
    )

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    content = Column(Text)
    sender_type = Column(String)  # user, agent, system
    sender_id = Column(String)
    agent_id = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    escalated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default={})
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_message_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_message_sender_type', 'sender_type'),
    )

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    status = Column(String, default="idle")  # idle, busy, offline
    specialization = Column(String, nullable=True)  # general, technical, sales, etc.
    current_load = Column(Integer, default=0)
    max_load = Column(Integer, default=5)
    total_messages_processed = Column(Integer, default=0)
    average_response_time_ms = Column(Float, default=0.0)
    average_confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default={})
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_agent_status', 'status'),
        Index('idx_agent_specialization', 'specialization'),
    )

class EscalationCase(Base):
    __tablename__ = "escalation_cases"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    message_id = Column(String, ForeignKey("messages.id"))
    reason = Column(String)  # low_confidence, explicit_request, complex_query, etc.
    assigned_human_id = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, assigned, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    extra_data = Column(JSON, default={})
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_escalation_status', 'status'),
        Index('idx_escalation_created_at', 'created_at'),
    )

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default={})
    
    # Add indexes for performance
    __table_args__ = (
        Index('idx_metrics_name_timestamp', 'metric_name', 'timestamp'),
    )

# Database engine and session management
engine = None
async_session_factory = None

async def init_db():
    """Initialize database connection and create tables"""
    global engine, async_session_factory
    
    try:
        logger.info("Initializing database connection")
        
        # Create async engine
        # Use SQLite for local development if no PostgreSQL URL provided
        database_url = settings.DATABASE_URL
        if not database_url or database_url.startswith("postgresql"):
            database_url = "sqlite+aiosqlite:///./agentic_comms.db"
            logger.info("Using SQLite database for local development")
        
        engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
        
        # Create session factory
        async_session_factory = async_sessionmaker(
            engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection"""
    if not async_session_factory:
        raise RuntimeError("Database not initialized")
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db():
    """Close database connections"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")

# Helper functions for common database operations
async def get_conversation_by_id(db: AsyncSession, conversation_id: str) -> Conversation:
    """Get conversation by ID"""
    from sqlalchemy import select
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()

async def get_messages_by_conversation(
    db: AsyncSession, 
    conversation_id: str, 
    limit: int = 50
) -> list[Message]:
    """Get messages for a conversation"""
    from sqlalchemy import select
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()

async def get_active_agents(db: AsyncSession) -> list[Agent]:
    """Get all active agents"""
    from sqlalchemy import select
    result = await db.execute(
        select(Agent)
        .where(Agent.status.in_(["idle", "busy"]))
        .order_by(Agent.current_load.asc())
    )
    return result.scalars().all()

async def create_message(
    db: AsyncSession,
    message_data: dict
) -> Message:
    """Create a new message"""
    message = Message(**message_data)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

async def update_agent_status(
    db: AsyncSession,
    agent_id: str,
    status: str,
    current_load: int = None
) -> Agent:
    """Update agent status and load"""
    from sqlalchemy import select
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    
    if agent:
        agent.status = status
        agent.last_activity = datetime.utcnow()
        if current_load is not None:
            agent.current_load = current_load
        await db.commit()
        await db.refresh(agent)
    
    return agent 