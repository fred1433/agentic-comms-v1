import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
import structlog
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime
import uuid

from config import settings
from database import init_db, get_db_session
from models import Message, Conversation, Agent, User
from services.llm_service import LLMService
from services.vector_service import VectorService
from services.voice_service import VoiceService
from services.email_service import EmailService
from services.agent_orchestrator import AgentOrchestrator
from utils.logging import setup_logging
from utils.metrics import metrics_registry

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Global services
redis_client = None
agent_orchestrator = None
llm_service = None
vector_service = None
voice_service = None
email_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global redis_client, agent_orchestrator, llm_service, vector_service, voice_service, email_service
    
    logger.info("Starting Agentic Communications API Gateway")
    
    # Initialize Redis connection
    redis_client = redis.from_url(settings.REDIS_URL)
    await redis_client.ping()
    logger.info("Redis connection established")
    
    # Initialize services
    llm_service = LLMService()
    vector_service = VectorService()
    voice_service = VoiceService()
    email_service = EmailService()
    
    # Initialize agent orchestrator
    agent_orchestrator = AgentOrchestrator(redis_client, llm_service, vector_service)
    await agent_orchestrator.start()
    logger.info("Agent orchestrator started")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down services")
    if agent_orchestrator:
        await agent_orchestrator.stop()
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Agentic Communications API",
    description="Multi-channel AI agents system for email, chat, and voice communications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    conversation_id: Optional[str] = None
    user_id: str
    channel: str = "chat"
    metadata: Optional[dict] = None

class EmailMessage(BaseModel):
    subject: str
    content: str
    from_email: EmailStr
    to_email: EmailStr
    conversation_id: Optional[str] = None
    metadata: Optional[dict] = None

class VoiceMessage(BaseModel):
    conversation_id: Optional[str] = None
    user_id: str
    metadata: Optional[dict] = None

class MessageResponse(BaseModel):
    id: str
    content: str
    response_time_ms: int
    confidence_score: float
    agent_id: str
    escalated: bool
    conversation_id: str

class ConversationSummary(BaseModel):
    id: str
    channel: str
    message_count: int
    last_activity: datetime
    status: str
    resolution_rate: float

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await redis_client.ping()
        return {
            "status": "healthy",
            "services": {
                "redis": "connected",
                "database": "connected",
                "agents": f"{await agent_orchestrator.get_active_agent_count()} active"
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Chat endpoint
@app.post("/api/v1/chat", response_model=MessageResponse)
async def send_chat_message(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Send a chat message and get AI agent response"""
    start_time = datetime.utcnow()
    
    try:
        # Create or get conversation
        if not message.conversation_id:
            message.conversation_id = str(uuid.uuid4())
        
        # Queue message for processing
        result = await agent_orchestrator.process_message({
            "id": str(uuid.uuid4()),
            "conversation_id": message.conversation_id,
            "content": message.content,
            "user_id": message.user_id,
            "channel": message.channel,
            "timestamp": start_time.isoformat(),
            "metadata": message.metadata or {}
        })
        
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Log metrics
        background_tasks.add_task(
            metrics_registry.record_response_time,
            response_time_ms,
            message.channel
        )
        
        return MessageResponse(
            id=result["id"],
            content=result["content"],
            response_time_ms=response_time_ms,
            confidence_score=result["confidence_score"],
            agent_id=result["agent_id"],
            escalated=result["escalated"],
            conversation_id=message.conversation_id
        )
        
    except Exception as e:
        logger.error("Chat message processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")

# Email endpoint
@app.post("/api/v1/email", response_model=MessageResponse)
async def send_email_message(
    message: EmailMessage,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Process incoming email and generate AI response"""
    start_time = datetime.utcnow()
    
    try:
        # Create conversation ID from email thread
        if not message.conversation_id:
            message.conversation_id = f"email_{hash(f'{message.from_email}_{message.subject}')}"
        
        # Queue email for processing
        result = await agent_orchestrator.process_message({
            "id": str(uuid.uuid4()),
            "conversation_id": message.conversation_id,
            "content": f"Subject: {message.subject}\n\n{message.content}",
            "user_id": message.from_email,
            "channel": "email",
            "timestamp": start_time.isoformat(),
            "metadata": {
                "from_email": message.from_email,
                "to_email": message.to_email,
                "subject": message.subject,
                **(message.metadata or {})
            }
        })
        
        # Send email response
        background_tasks.add_task(
            email_service.send_response,
            message.from_email,
            f"Re: {message.subject}",
            result["content"]
        )
        
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return MessageResponse(
            id=result["id"],
            content=result["content"],
            response_time_ms=response_time_ms,
            confidence_score=result["confidence_score"],
            agent_id=result["agent_id"],
            escalated=result["escalated"],
            conversation_id=message.conversation_id
        )
        
    except Exception as e:
        logger.error("Email processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process email")

# Voice WebSocket endpoint
@app.websocket("/api/v1/voice/{conversation_id}")
async def voice_websocket(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time voice communication"""
    await websocket.accept()
    logger.info("Voice WebSocket connected", conversation_id=conversation_id)
    
    try:
        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()
            
            # Process speech-to-text
            transcript = await voice_service.speech_to_text(audio_data)
            
            if transcript:
                # Process with AI agent
                result = await agent_orchestrator.process_message({
                    "id": str(uuid.uuid4()),
                    "conversation_id": conversation_id,
                    "content": transcript,
                    "user_id": "voice_user",
                    "channel": "voice",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {"source": "voice"}
                })
                
                # Convert response to speech
                audio_response = await voice_service.text_to_speech(result["content"])
                
                # Send back audio + text
                await websocket.send_json({
                    "type": "response",
                    "transcript": transcript,
                    "response_text": result["content"],
                    "agent_id": result["agent_id"],
                    "confidence": result["confidence_score"]
                })
                
                await websocket.send_bytes(audio_response)
                
    except Exception as e:
        logger.error("Voice WebSocket error", error=str(e))
        await websocket.close()

# Voice upload endpoint (alternative to WebSocket)
@app.post("/api/v1/voice/upload")
async def upload_voice_message(
    audio_file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    user_id: str = "voice_user"
):
    """Upload audio file for processing"""
    try:
        audio_data = await audio_file.read()
        
        # Speech to text
        transcript = await voice_service.speech_to_text(audio_data)
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Process with AI agent
        result = await agent_orchestrator.process_message({
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "content": transcript,
            "user_id": user_id,
            "channel": "voice",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"source": "upload", "filename": audio_file.filename}
        })
        
        # Generate speech response
        audio_response = await voice_service.text_to_speech(result["content"])
        
        return StreamingResponse(
            iter([audio_response]),
            media_type="audio/wav",
            headers={
                "X-Transcript": transcript,
                "X-Response-Text": result["content"],
                "X-Agent-ID": result["agent_id"],
                "X-Conversation-ID": conversation_id
            }
        )
        
    except Exception as e:
        logger.error("Voice upload processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process voice message")

# Conversations endpoints
@app.get("/api/v1/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    channel: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get conversation summaries"""
    try:
        conversations = await agent_orchestrator.get_conversations(
            limit=limit,
            offset=offset,
            channel=channel
        )
        return conversations
    except Exception as e:
        logger.error("Failed to fetch conversations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation_details(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed conversation history"""
    try:
        conversation = await agent_orchestrator.get_conversation_details(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch conversation details", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")

# Dashboard & metrics endpoints
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        return await agent_orchestrator.get_dashboard_stats()
    except Exception as e:
        logger.error("Failed to fetch dashboard stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    try:
        return await agent_orchestrator.get_agents_status()
    except Exception as e:
        logger.error("Failed to fetch agents status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch agents status")

# Admin endpoints
@app.post("/api/v1/admin/scale-agents")
async def scale_agents(target_count: int):
    """Manually scale the number of agents"""
    try:
        await agent_orchestrator.scale_agents(target_count)
        return {"message": f"Scaling to {target_count} agents"}
    except Exception as e:
        logger.error("Failed to scale agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to scale agents")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_config=None  # Use our custom logging
    ) 