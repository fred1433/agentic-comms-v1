from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import uvicorn
import os

# Configuration pour Glitch
app = FastAPI(title="Agentic Communications V1", version="1.0.0")

# CORS très permissif pour la démo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    confidence: float
    timestamp: float

@app.get("/")
async def root():
    return {"message": "🚀 Agentic Communications Backend - Ready!", "status": "online"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "agentic-comms-backend",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.get("/api/v1/dashboard/stats")
async def dashboard_stats():
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

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    # Réponses intelligentes selon le message
    msg = request.message.lower()
    
    if "bonjour" in msg or "hello" in msg:
        response = "Bonjour ! Comment puis-je vous aider aujourd'hui ?"
    elif "prix" in msg or "tarif" in msg or "price" in msg:
        response = "Nos tarifs commencent à 100€/mois pour 1000 agents. Voulez-vous une démo personnalisée ?"
    elif "problème" in msg or "erreur" in msg or "bug" in msg:
        response = "Je vais vous aider à résoudre ce problème. Pouvez-vous me donner plus de détails ?"
    elif "demo" in msg or "test" in msg:
        response = "Parfait ! Vous êtes en train de tester notre système IA en temps réel. Tout fonctionne !"
    else:
        response = f"Merci pour votre message : '{request.message}'. Notre IA analyse votre demande..."
    
    return ChatResponse(
        response=response,
        conversation_id=f"conv_{int(time.time())}",
        confidence=0.87,
        timestamp=time.time()
    )

@app.get("/api/v1/agents/status")
async def agents_status():
    return {
        "active_agents": 45,
        "total_capacity": 1000,
        "queue_length": 3,
        "avg_response_time": 2.1
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 