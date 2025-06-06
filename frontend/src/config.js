// Configuration pour l'API
export const API_BASE_URL = 'https://agentic-comms-backend.fly.dev';

export default {
  apiUrl: API_BASE_URL,
  endpoints: {
    health: '/health',
    chat: '/api/v1/chat',
    dashboard: '/api/v1/dashboard/stats',
    agents: '/api/v1/agents/status'
  }
}; 