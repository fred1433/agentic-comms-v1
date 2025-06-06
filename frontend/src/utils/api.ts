import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { 
  ChatMessage, 
  EmailMessage, 
  MessageResponse, 
  DashboardStats, 
  Agent, 
  Conversation,
  ApiError 
} from '../types';

class ApiClient {
  private instance: AxiosInstance;
  
  constructor() {
    this.instance = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        
        // Don't show toast for health checks
        if (!error.config?.url?.includes('/health')) {
          toast.error(message);
        }
        
        const apiError: ApiError = {
          message,
          status: error.response?.status || 500,
          details: error.response?.data,
        };
        
        return Promise.reject(apiError);
      }
    );
  }
  
  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.instance.get('/health');
    return response.data;
  }
  
  // Chat endpoints
  async sendChatMessage(message: ChatMessage): Promise<MessageResponse> {
    const response = await this.instance.post('/api/v1/chat', message);
    return response.data;
  }
  
  // Email endpoints
  async sendEmailMessage(message: EmailMessage): Promise<MessageResponse> {
    const response = await this.instance.post('/api/v1/email', message);
    return response.data;
  }
  
  // Voice endpoints
  async uploadVoiceMessage(
    audioFile: File, 
    conversationId?: string, 
    userId: string = 'demo_user'
  ): Promise<Blob> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }
    formData.append('user_id', userId);
    
    const response = await this.instance.post('/api/v1/voice/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob',
    });
    
    return response.data;
  }
  
  // Dashboard endpoints
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.instance.get('/api/v1/dashboard/stats');
    return response.data;
  }
  
  // Agent endpoints
  async getAgentsStatus(): Promise<Agent[]> {
    const response = await this.instance.get('/api/v1/agents/status');
    return response.data;
  }
  
  async scaleAgents(targetCount: number): Promise<{ message: string }> {
    const response = await this.instance.post('/api/v1/admin/scale-agents', {
      target_count: targetCount,
    });
    return response.data;
  }
  
  // Conversation endpoints
  async getConversations(
    limit: number = 50, 
    offset: number = 0, 
    channel?: string
  ): Promise<Conversation[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (channel) {
      params.append('channel', channel);
    }
    
    const response = await this.instance.get(`/api/v1/conversations?${params}`);
    return response.data;
  }
  
  async getConversationDetails(conversationId: string): Promise<any> {
    const response = await this.instance.get(`/api/v1/conversations/${conversationId}`);
    return response.data;
  }
  
  // Metrics endpoint (Prometheus format)
  async getMetrics(): Promise<string> {
    const response = await this.instance.get('/metrics', {
      headers: {
        'Accept': 'text/plain',
      },
    });
    return response.data;
  }
}

// Create and export singleton instance
export const apiClient = new ApiClient();

// Utility functions for common operations
export const chatUtils = {
  async sendMessage(content: string, userId: string = 'demo_user'): Promise<MessageResponse> {
    return apiClient.sendChatMessage({
      content,
      user_id: userId,
      channel: 'chat',
    });
  },
  
  async sendEmailDemo(
    subject: string = 'Demo Support Request',
    content: string,
    fromEmail: string = 'customer@example.com'
  ): Promise<MessageResponse> {
    return apiClient.sendEmailMessage({
      subject,
      content,
      from_email: fromEmail,
      to_email: 'support@company.com',
    });
  },
};

export const agentUtils = {
  async autoScale(load: number): Promise<void> {
    // Simple auto-scaling logic based on load
    let targetAgents = 50; // Base agents
    
    if (load > 100) targetAgents = 200;
    if (load > 500) targetAgents = 500;
    if (load > 1000) targetAgents = 1000;
    
    await apiClient.scaleAgents(targetAgents);
    toast.success(`Scaled to ${targetAgents} agents`);
  },
  
  getStatusColor(status: string): string {
    switch (status) {
      case 'idle': return 'text-success-600';
      case 'busy': return 'text-warning-600';
      case 'error': return 'text-danger-600';
      case 'offline': return 'text-gray-400';
      default: return 'text-gray-600';
    }
  },
  
  getStatusIcon(status: string): string {
    switch (status) {
      case 'idle': return 'status-online';
      case 'busy': return 'status-busy';
      case 'error': return 'status-error';
      case 'offline': return 'status-offline';
      default: return 'status-offline';
    }
  },
};

export const formatUtils = {
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  },
  
  formatNumber(num: number): string {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  },
  
  formatPercentage(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
  },
  
  formatResponseTime(ms: number): string {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`;
    }
    return `${(ms / 1000).toFixed(1)}s`;
  },
};

export default apiClient; 