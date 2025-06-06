export interface Message {
  id: string;
  content: string;
  sender_type: 'user' | 'agent' | 'system';
  sender_id: string;
  agent_id?: string;
  confidence_score?: number;
  response_time_ms?: number;
  escalated: boolean;
  created_at: string;
  conversation_id: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  user_id: string;
  channel: 'email' | 'chat' | 'voice';
  status: 'active' | 'resolved' | 'escalated';
  created_at: string;
  updated_at: string;
  message_count: number;
  last_activity: string;
  resolution_rate: number;
  metadata?: Record<string, any>;
}

export interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'busy' | 'offline' | 'error';
  specialization: 'general' | 'technical' | 'sales';
  current_load: number;
  max_load: number;
  total_processed: number;
  errors: number;
  current_task?: string;
  last_activity: string;
  success_rate: number;
  average_response_time_ms: number;
  average_confidence_score: number;
}

export interface ChatMessage {
  content: string;
  conversation_id?: string;
  user_id: string;
  channel: string;
  metadata?: Record<string, any>;
}

export interface EmailMessage {
  subject: string;
  content: string;
  from_email: string;
  to_email: string;
  conversation_id?: string;
  metadata?: Record<string, any>;
}

export interface MessageResponse {
  id: string;
  content: string;
  response_time_ms: number;
  confidence_score: number;
  agent_id: string;
  escalated: boolean;
  conversation_id: string;
}

export interface DashboardStats {
  total_agents: number;
  agent_status: Record<string, number>;
  total_messages_processed: number;
  total_escalations: number;
  resolution_rate: number;
  average_response_time_ms: number;
  pending_messages: number;
  uptime_seconds: number;
  messages_per_minute: number;
}

export interface VoiceRecording {
  blob: Blob;
  duration: number;
  transcript?: string;
}

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, any>;
}

export interface MetricCard {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'positive' | 'negative' | 'neutral';
    label: string;
  };
  icon?: React.ComponentType<{ className?: string }>;
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'gray';
}

export interface WebSocketMessage {
  type: 'response' | 'status' | 'error';
  transcript?: string;
  response_text?: string;
  agent_id?: string;
  confidence?: number;
  audio_data?: ArrayBuffer;
}

export type NotificationType = 'success' | 'error' | 'info' | 'warning'; 