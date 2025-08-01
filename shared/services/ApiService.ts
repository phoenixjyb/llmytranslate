// Unified API service for both web and React Native platforms
// This ensures identical API calls and responses across platforms

export interface TranslationRequest {
  text: string;
  target_lang: string;
  source_lang: string;
}

export interface TranslationResponse {
  translated_text: string;
  source_lang: string;
  target_lang: string;
  original_text: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  model?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
  timestamp: string;
}

export interface TTSRequest {
  text: string;
  language?: string;
  voice?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  services: {
    translation: boolean;
    chat: boolean;
    tts: boolean;
  };
}

export class ApiService {
  private baseUrl: string;
  
  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Translation service - identical for both platforms
  async translate(text: string, targetLang: string = 'en', sourceLang: string = 'auto'): Promise<TranslationResponse> {
    const response = await fetch(`${this.baseUrl}/api/optimized/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        target_lang: targetLang,
        source_lang: sourceLang,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Translation failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Chat service - identical for both platforms
  async sendChatMessage(message: string, conversationId?: string, model: string = 'gemma3:latest'): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        model,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Chat failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // TTS service - identical for both platforms
  async textToSpeech(text: string, language: string = 'en', voice?: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/tts/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        language,
        voice,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`TTS failed: ${response.statusText}`);
    }
    
    return response.blob(); // Returns audio data
  }

  // Voice chat service
  async sendVoiceMessage(audioBlob: Blob, conversationId?: string): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    if (conversationId) {
      formData.append('conversation_id', conversationId);
    }

    const response = await fetch(`${this.baseUrl}/api/voice/message`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Voice message failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Phone call simulation
  async startPhoneCall(): Promise<{ call_id: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/api/phone/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Phone call start failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async endPhoneCall(callId: string): Promise<{ duration: number; status: string }> {
    const response = await fetch(`${this.baseUrl}/api/phone/end`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ call_id: callId }),
    });
    
    if (!response.ok) {
      throw new Error(`Phone call end failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Health check - identical for both platforms
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Service info - identical for both platforms
  async getServiceInfo(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/info`);
    
    if (!response.ok) {
      throw new Error(`Service info failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Conversation management
  async getConversations(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/chat/conversations`);
    
    if (!response.ok) {
      throw new Error(`Get conversations failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  async deleteConversation(conversationId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/chat/conversations/${conversationId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`Delete conversation failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Language detection
  async detectLanguage(text: string): Promise<{ language: string; confidence: number }> {
    const response = await fetch(`${this.baseUrl}/api/translate/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      throw new Error(`Language detection failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Get available languages
  async getAvailableLanguages(): Promise<{ code: string; name: string }[]> {
    const response = await fetch(`${this.baseUrl}/api/translate/languages`);
    
    if (!response.ok) {
      throw new Error(`Get languages failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // Get available models
  async getAvailableModels(): Promise<{ value: string; label: string; description?: string }[]> {
    const response = await fetch(`${this.baseUrl}/api/chat/models`);
    
    if (!response.ok) {
      throw new Error(`Get models failed: ${response.statusText}`);
    }
    
    return response.json();
  }
}

// Create a default instance for easy importing
export const apiService = new ApiService();
