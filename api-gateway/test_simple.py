from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import time
import json
import random
from datetime import datetime
import os
from openai import OpenAI

# Initialize OpenAI client
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
    else:
        print("⚠️  OpenAI API key not found - using mock responses")
except Exception as e:
    print(f"⚠️  OpenAI initialization failed: {e}")

app = FastAPI(title="Agentic Communications V1 - Production Ready", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    confidence: float
    response_time: float
    timestamp: float
    agent_id: str

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    priority: Optional[str] = "normal"

class DashboardStats(BaseModel):
    active_agents: int
    total_conversations: int
    avg_response_time: float
    auto_resolution_rate: float
    queue_length: int
    uptime_hours: float

# In-memory storage for demo
conversations = {}
metrics = {
    "total_conversations": 0,
    "total_messages": 0,
    "response_times": [],
    "start_time": time.time()
}

# Mock conversation context for realistic responses
SYSTEM_PROMPT = """You are an intelligent customer service AI assistant for Agentic Communications.
You help customers with support questions, product information, and technical issues.
Keep responses helpful, professional, and concise. If you cannot help with something, politely escalate to a human agent.
Current company info: We provide AI-powered multi-channel communication solutions (email, chat, voice)."""

async def get_ai_response(message: str, conversation_history: List = None) -> tuple[str, float]:
    """Get response from OpenAI or fallback to mock"""
    start_time = time.time()
    
    if openai_client:
        try:
            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    messages.append(msg)
            
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            confidence = 0.85 + random.uniform(0, 0.15)  # Simulate confidence scoring
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to mock response
            ai_response = get_mock_response(message)
            confidence = 0.75
    else:
        # Mock response system
        ai_response = get_mock_response(message)
        confidence = 0.75
    
    response_time = time.time() - start_time
    return ai_response, confidence, response_time

def get_mock_response(message: str) -> str:
    """Smart mock responses based on message content"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "hey", "bonjour"]):
        return "Hello! I'm your AI assistant. How can I help you today with your communication needs?"
    
    elif any(word in message_lower for word in ["price", "pricing", "cost", "tarif"]):
        return "Our pricing starts at $100/month for up to 1000 concurrent agents. We offer custom enterprise plans. Would you like me to connect you with our sales team for a detailed quote?"
    
    elif any(word in message_lower for word in ["problem", "issue", "error", "bug", "problème"]):
        return "I'm sorry to hear you're experiencing issues. Can you provide more details about the specific problem you're encountering? I'll do my best to help resolve it quickly."
    
    elif any(word in message_lower for word in ["feature", "functionality", "capability"]):
        return "Our platform provides multi-channel AI communication (email, chat, voice), real-time agent orchestration, vector-based memory, and intelligent escalation. What specific feature interests you?"
    
    elif any(word in message_lower for word in ["demo", "test", "try"]):
        return "Great! You're already using our demo system. You can see real-time metrics, test our AI chat, and explore the dashboard. Would you like me to show you specific features?"
    
    else:
        return f"Thank you for your message: '{message[:100]}...' I understand you're asking about our AI communication platform. Our system handles email, chat, and voice channels with auto-scaling up to 1000 concurrent agents. How can I assist you further?"

# API Endpoints
@app.get("/health")
async def health_check():
    """Enhanced health check with system status"""
    return {
        "status": "healthy",
        "service": "agentic-comms-backend",
        "openai_status": "connected" if openai_client else "mock_mode",
        "uptime_hours": round((time.time() - metrics["start_time"]) / 3600, 2),
        "total_conversations": metrics["total_conversations"],
        "version": "1.0.0"
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Intelligent chat endpoint with OpenAI integration"""
    
    # Generate conversation ID if not provided
    if not request.conversation_id:
        request.conversation_id = f"conv_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Get or create conversation history
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = []
        metrics["total_conversations"] += 1
    
    # Add user message to history
    conversations[request.conversation_id].append({
        "role": "user", 
        "content": request.message,
        "timestamp": time.time()
    })
    
    # Get AI response
    ai_response, confidence, response_time = await get_ai_response(
        request.message, 
        conversations[request.conversation_id]
    )
    
    # Add AI response to history
    conversations[request.conversation_id].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": time.time()
    })
    
    # Update metrics
    metrics["total_messages"] += 1
    metrics["response_times"].append(response_time)
    
    # Keep only last 50 response times for rolling average
    if len(metrics["response_times"]) > 50:
        metrics["response_times"] = metrics["response_times"][-50:]
    
    agent_id = f"agent_{random.randint(100, 999)}"
    
    return ChatResponse(
        response=ai_response,
        conversation_id=request.conversation_id,
        confidence=confidence,
        response_time=response_time,
        timestamp=time.time(),
        agent_id=agent_id
    )

@app.get("/api/v1/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Real-time dashboard statistics"""
    
    # Calculate metrics
    avg_response_time = sum(metrics["response_times"]) / len(metrics["response_times"]) if metrics["response_times"] else 0
    auto_resolution_rate = 0.83 + random.uniform(-0.05, 0.05)  # Simulate ~83% resolution rate
    active_agents = 45 + random.randint(-5, 15)  # Simulate agent scaling
    queue_length = max(0, random.randint(0, 8))  # Realistic queue
    uptime_hours = (time.time() - metrics["start_time"]) / 3600
    
    return DashboardStats(
        active_agents=active_agents,
        total_conversations=metrics["total_conversations"],
        avg_response_time=round(avg_response_time, 3),
        auto_resolution_rate=round(auto_resolution_rate, 3),
        queue_length=queue_length,
        uptime_hours=round(uptime_hours, 2)
    )

@app.post("/api/v1/email")
async def send_email(request: EmailRequest):
    """Email handling simulation with AI processing"""
    
    # Simulate email processing time
    processing_time = random.uniform(0.5, 2.0)
    
    # Generate AI response to email
    ai_response, confidence, _ = await get_ai_response(request.body)
    
    metrics["total_messages"] += 1
    
    return {
        "status": "processed",
        "message": f"Email to {request.to} processed successfully",
        "subject": request.subject,
        "ai_response": ai_response,
        "confidence": confidence,
        "processing_time": round(processing_time, 3),
        "timestamp": time.time(),
        "priority": request.priority
    }

@app.get("/api/v1/conversations")
async def get_conversations():
    """Get conversation history for dashboard"""
    conversation_list = []
    for conv_id, messages in list(conversations.items())[-10:]:  # Last 10 conversations
        if messages:
            last_message = messages[-1]
            conversation_list.append({
                "id": conv_id,
                "last_message": last_message["content"][:100] + "..." if len(last_message["content"]) > 100 else last_message["content"],
                "message_count": len(messages),
                "last_activity": last_message["timestamp"],
                "status": "active" if time.time() - last_message["timestamp"] < 300 else "completed"
            })
    
    return {"conversations": conversation_list}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Agentic Communications V1 - Production Backend")
    print("🤖 OpenAI Integration:", "✅ Active" if openai_client else "⚠️  Mock Mode")
    print("🌐 CORS enabled for: http://localhost:3000")
    print("📊 Endpoints: /health, /api/v1/chat, /api/v1/dashboard/stats, /api/v1/email")
    uvicorn.run(app, host="127.0.0.1", port=8000) 