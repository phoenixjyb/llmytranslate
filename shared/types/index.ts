// Shared TypeScript types for both web and React Native platforms
// This ensures type consistency across all platforms

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp?: string;
}

// Translation Types
export interface TranslationRequest {
  text: string;
  source_lang: string;
  target_lang: string;
  user_id?: string;
}

export interface TranslationResponse {
  translatedText: string;
  sourceLanguage: string;
  targetLanguage: string;
  originalText: string;
  confidence?: number;
  duration?: number;
}

export interface Language {
  code: string;
  name: string;
  flag?: string;
  native_name?: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  message: string;
  response?: string;
  timestamp: string;
  user_id?: string;
  conversation_id?: string;
  model?: string;
  role: 'user' | 'assistant' | 'system';
  metadata?: {
    tokens_used?: number;
    response_time?: number;
    model_info?: string;
  };
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  user_id?: string;
  model?: string;
  system_prompt?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  model: string;
  tokens_used?: number;
  response_time?: number;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  user_id?: string;
  model?: string;
}

// Model Types
export interface AIModel {
  value: string;
  label: string;
  description: string;
  provider: string;
  capabilities: string[];
  context_window?: number;
  max_tokens?: number;
  cost_per_token?: number;
}

// TTS (Text-to-Speech) Types
export interface TTSRequest {
  text: string;
  voice?: string;
  speed?: number;
  language?: string;
  format?: 'mp3' | 'wav' | 'ogg';
}

export interface TTSResponse {
  audio_url: string;
  duration: number;
  format: string;
  size: number;
  text: string;
}

// Voice Chat Types
export interface VoiceMessage {
  id: string;
  audio_url?: string;
  transcript: string;
  response_text: string;
  response_audio_url?: string;
  timestamp: string;
  duration?: number;
  language?: string;
}

export interface VoiceRequest {
  audio_data?: string;
  text?: string;
  language?: string;
  conversation_id?: string;
}

// Phone Call Types
export interface PhoneCall {
  id: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'ended';
  started_at: string;
  ended_at?: string;
  duration: number;
  participant_count: number;
  call_type: 'incoming' | 'outgoing' | 'conference';
}

export interface CallRequest {
  action: 'start' | 'end' | 'status';
  call_id?: string;
  user_id?: string;
  call_type?: 'voice' | 'video';
}

export interface CallResponse {
  call_id: string;
  status: PhoneCall['status'];
  message: string;
  duration?: number;
  connection_info?: {
    server: string;
    room: string;
    token?: string;
  };
}

// User Types
export interface User {
  id: string;
  username?: string;
  email?: string;
  created_at: string;
  last_active?: string;
  preferences?: UserPreferences;
  is_guest?: boolean;
}

export interface UserPreferences {
  default_language?: string;
  preferred_model?: string;
  voice_settings?: {
    voice: string;
    speed: number;
    volume: number;
  };
  theme?: 'light' | 'dark' | 'auto';
  auto_translate?: boolean;
  notification_settings?: {
    sound: boolean;
    vibration: boolean;
    popup: boolean;
  };
}

// Service Types
export interface Service {
  id: string;
  name: string;
  icon: string;
  description: string;
  features: string[];
  gradient: {
    start: string;
    end: string;
  };
  status?: 'active' | 'inactive' | 'maintenance';
  endpoint?: string;
}

// Application State Types
export interface AppState {
  isLoading: boolean;
  error?: string;
  user?: User;
  currentService?: string;
  isOnline: boolean;
  theme: 'light' | 'dark' | 'auto';
}

// Navigation Types (React Native specific but can be used by web)
export interface NavigationParams {
  HomeScreen: undefined;
  TranslateScreen: {
    initialText?: string;
    sourceLang?: string;
    targetLang?: string;
  };
  ChatScreen: {
    conversationId?: string;
    initialMessage?: string;
  };
  VoiceChatScreen: {
    autoStart?: boolean;
    language?: string;
  };
  PhoneCallScreen: {
    callId?: string;
    incoming?: boolean;
  };
}

// Platform-specific Types
export interface PlatformInfo {
  platform: 'web' | 'ios' | 'android' | 'windows' | 'macos' | 'linux';
  version: string;
  userAgent?: string;
  screen: {
    width: number;
    height: number;
    scale: number;
  };
  capabilities: {
    audio: boolean;
    video: boolean;
    notifications: boolean;
    location: boolean;
    camera: boolean;
    microphone: boolean;
  };
}

// Configuration Types
export interface AppConfig {
  apiBaseUrl: string;
  environment: 'development' | 'staging' | 'production';
  version: string;
  buildNumber?: string;
  features: {
    [key: string]: boolean;
  };
  limits: {
    maxMessageLength: number;
    maxTranslationLength: number;
    maxFileSize: number;
    rateLimit: {
      requests: number;
      window: number;
    };
  };
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  context?: {
    component?: string;
    action?: string;
    user_id?: string;
  };
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'message' | 'status' | 'error' | 'ping' | 'pong';
  data: any;
  timestamp: string;
  id?: string;
}

export interface WebSocketConnection {
  isConnected: boolean;
  reconnectAttempts: number;
  lastMessage?: string;
  subscriptions: string[];
}

// Analytics Types
export interface AnalyticsEvent {
  name: string;
  properties?: { [key: string]: any };
  timestamp: string;
  user_id?: string;
  session_id?: string;
}

// Performance Types
export interface PerformanceMetrics {
  api_response_time: number;
  render_time: number;
  memory_usage: number;
  network_latency: number;
  error_rate: number;
  user_interactions: number;
}

// Storage Types
export interface StorageItem<T = any> {
  key: string;
  value: T;
  expires?: number;
  created: number;
  accessed: number;
}

// Utility Types
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
export type Partial<T> = { [P in keyof T]?: T[P] };
export type Required<T> = { [P in keyof T]-?: T[P] };

// Event Types
export type EventListener<T = any> = (data: T) => void;
export type EventMap = { [key: string]: any };

// Generic API Types
export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
export type ContentType = 'application/json' | 'multipart/form-data' | 'text/plain';

export interface RequestConfig {
  method: HTTPMethod;
  headers?: { [key: string]: string };
  body?: any;
  timeout?: number;
  retries?: number;
  contentType?: ContentType;
}

// Export all defined types for easy importing
// All types are already exported via their individual interface/type declarations above
