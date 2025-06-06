# 🚀 Quick Start Guide - Agentic Communications V1

## Prerequisites

1. **Python 3.9+** and **Node.js 18+**
2. **API Keys** (required):
   ```bash
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   DEEPGRAM_API_KEY=your_key
   PINECONE_API_KEY=your_key
   ```
3. **Services** (for production):
   - Railway account (PostgreSQL + Redis)
   - Surge CLI for frontend deployment

## 🎯 48-Hour Demo Setup

### 1. Environment Setup (5 min)
```bash
# Clone and setup
git clone <your-repo>
cd agentic-comms-v1

# Copy environment file
cp env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup (10 min)
```bash
# Install Python dependencies
cd api-gateway
pip install -r requirements.txt

# Setup local database (optional - can use Railway)
# Default uses PostgreSQL on Railway

# Start API server
python main.py
# Server runs on http://localhost:8000
```

### 3. Frontend Setup (5 min)
```bash
# Install Node dependencies
cd ../frontend
npm install

# Start development server
npm start
# Frontend runs on http://localhost:3000
```

### 4. Quick Test (2 min)
```bash
# Test API health
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "user_id": "demo"}'
```

## 🎬 Demo Workflow

### Live Demo Script (5 minutes)

1. **Open Dashboard** (`/dashboard`)
   - Show real-time metrics
   - Agent count auto-scaling
   - Response time <5s

2. **Chat Interface** (`/console`)
   - Send message: "I need help with my order"
   - AI responds in <5s with context

3. **Voice Demo** (`/voice`)
   - Click record button
   - Say: "What's your return policy?"
   - Hear AI response in <1s

4. **Email Simulation**
   ```bash
   curl -X POST http://localhost:8000/api/v1/email \
     -H "Content-Type: application/json" \
     -d '{
       "from_email": "customer@example.com",
       "to_email": "support@company.com", 
       "subject": "Order Issue",
       "content": "My order #12345 is delayed. Can you help?"
     }'
   ```

5. **Agents Status** (`/agents`)
   - Show 500+ agents active
   - Auto-scaling in action
   - Resolution rate >80%

## 🔧 Development Mode

### Hot Reload Setup
```bash
# Terminal 1: Backend with hot reload
cd api-gateway
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend with hot reload  
cd frontend
npm start

# Terminal 3: Redis (if local)
redis-server

# Terminal 4: PostgreSQL (if local)
psql -U postgres -d agentic_comms
```

### Environment Variables
```bash
# Development (local)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/agentic_comms
REDIS_URL=redis://localhost:6379

# Production (Railway)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/railway
REDIS_URL=redis://user:pass@host:6379
```

## 🚀 Production Deployment

### Backend (Railway)
```bash
# Connect to Railway
railway login
railway init

# Deploy API
railway up

# Set environment variables in Railway dashboard
```

### Frontend (Surge)
```bash
# Install Surge CLI
npm install -g surge

# Build and deploy
cd frontend
npm run build
surge build/ agentic-comms-v1.surge.sh
```

## 📊 Monitoring & Metrics

### Health Checks
- API Health: `GET /health`
- Metrics: `GET /metrics` (Prometheus format)
- Agent Status: `GET /api/v1/agents/status`

### Dashboard URLs
- **Frontend**: https://agentic-comms-v1.surge.sh
- **API**: https://agentic-comms-api.railway.app
- **Grafana**: (configured with Railway metrics)

## 🐛 Troubleshooting

### Common Issues

1. **API Keys Missing**
   ```bash
   # Check .env file
   cat .env | grep API_KEY
   ```

2. **Database Connection**
   ```bash
   # Test database URL
   python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
   ```

3. **Redis Connection**
   ```bash
   # Test Redis
   redis-cli ping
   ```

4. **Frontend Build Issues**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

### Performance Optimization

1. **Agent Scaling**
   ```python
   # Adjust in .env
   MAX_CONCURRENT_AGENTS=1000
   WORKER_POOL_SIZE=50
   ```

2. **Response Time**
   ```python
   # Optimize in .env
   MAX_RESPONSE_TIME_MS=3000  # Target <5s
   ```

## 📈 Success Metrics

### Demo Success Criteria
- ✅ API responds in <5s
- ✅ Voice latency <1s  
- ✅ 500+ agents active
- ✅ >80% auto-resolution
- ✅ Real-time dashboard updates
- ✅ Multi-channel (chat/email/voice) working

### Production Readiness
- ✅ Error handling
- ✅ Logging & monitoring
- ✅ Auto-scaling
- ✅ Data persistence
- ✅ Security headers
- ✅ Rate limiting ready

---

**Ready for demo in <30 minutes!** 🎉

Need help? Check `IMPLEMENTATION_STATUS.md` for detailed component status. 