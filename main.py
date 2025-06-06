import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time

# Configuration simple
app = FastAPI(title="Agentic Communications V1 - Backend", version="1.0.0")

# CORS pour autoriser les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet toutes les origines pour la démo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic simples
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    confidence: float
    timestamp: float

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

# Endpoints basiques
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agentic-comms-backend",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics (mock data for now)"""
    return {
        "metrics": {
            "avg_response_time": 2.1,
            "auto_resolution_rate": 0.85,
            "active_agents": 45,
            "total_conversations": 1234
        },
        "timestamps": {
            "last_updated": time.time()
        }
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Simple chat endpoint that returns a mock response"""
    
    # Simulation d'une réponse IA
    response_text = f"Merci pour votre message : '{request.message}'. Votre demande a été traitée par notre système IA."
    
    if "bonjour" in request.message.lower():
        response_text = "Bonjour ! Comment puis-je vous aider aujourd'hui ?"
    elif "prix" in request.message.lower() or "tarif" in request.message.lower():
        response_text = "Nos tarifs varient selon vos besoins. Pouvez-vous me donner plus de détails sur ce que vous recherchez ?"
    elif "problème" in request.message.lower() or "erreur" in request.message.lower():
        response_text = "Je suis désolé d'apprendre que vous rencontrez un problème. Pouvez-vous me décrire exactement ce qui ne fonctionne pas ?"
    
    return ChatResponse(
        response=response_text,
        conversation_id=f"conv_{int(time.time())}",
        confidence=0.87,
        timestamp=time.time()
    )

@app.post("/api/v1/email")
async def send_email(request: EmailRequest):
    """Simple email endpoint (mock for now)"""
    
    # Pour le moment, on simule l'envoi
    print(f"📧 Email simulé envoyé à {request.to}")
    print(f"📝 Sujet: {request.subject}")
    print(f"💬 Contenu: {request.body[:100]}...")
    
    return {
        "status": "sent",
        "message": f"Email envoyé avec succès à {request.to}",
        "timestamp": time.time()
    }

@app.get("/api/v1/agents/status")
async def get_agents_status():
    """Get agent status"""
    return {
        "active_agents": 45,
        "total_capacity": 1000,
        "queue_length": 3,
        "avg_response_time": 2.1
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 