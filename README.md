# Agentic Communications V1

## Architecture Overview

Multi-channel AI agents system for email, chat, and voice communications with auto-scaling capabilities.

### Tech Stack
- **Frontend**: React (deployed on Surge)
- **API Gateway**: FastAPI (deployed on Railway)
- **Workers**: Redis Streams + Agent Pool (Railway autoscale)
- **Vector DB**: Pinecone (contextual memory)
- **Database**: PostgreSQL (Railway)
- **Voice**: Deepgram STT/TTS
- **LLM**: Azure OpenAI GPT-4o
- **Observability**: Grafana Cloud + Tempo

### Project Structure
```
agentic-comms-v1/
├── frontend/              # React SPA for console + call widget
├── api-gateway/           # FastAPI backend
├── agent-workers/         # Multi-agent processor pool
├── vector-store/          # Pinecone integration
├── database/              # PostgreSQL schemas + migrations
├── observability/         # Grafana dashboards + alerts
├── deployment/            # Railway configs + CI/CD
├── data-generation/       # Mock data scripts
└── docs/                  # Architecture diagrams
```

### Key Features (V1)
1. **Unified Inbox** - Email + Chat with ≤5s response time
2. **Contextual Memory** - Vector DB per conversation thread
3. **Voice Integration** - Deepgram STT/TTS with <1s latency
4. **Multi-Agent Orchestration** - 1000+ concurrent agents
5. **Live Dashboard** - Real-time monitoring & logs
6. **Smart Escalation** - Intelligent human fallback

### Demo Target
- **48h deliverable**: Core inbox + voice loop + basic scaling
- **J3-J14**: Hardening + full observability + demo polish

### Getting Started
```bash
# Clone and setup
git clone <repo>
cd agentic-comms-v1

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with API keys

# Run development
npm run dev
```

### Environment Variables
```
# Azure OpenAI
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

# Deepgram
DEEPGRAM_API_KEY=

# Pinecone
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=

# Railway
DATABASE_URL=
REDIS_URL=

# Grafana
GRAFANA_API_KEY=
``` 