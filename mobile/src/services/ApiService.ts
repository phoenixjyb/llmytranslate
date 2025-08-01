// API service for communicating with FastAPI backend
export class ApiService {
  private baseUrl: string;
  
  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Translation service
  async translate(text: string, targetLang: string = 'en', sourceLang: string = 'auto') {
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

  // Chat service
  async sendChatMessage(message: string, conversationId?: string) {
    const response = await fetch(`${this.baseUrl}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Chat failed: ${response.statusText}`);
    }
    
    return response.json();
  }

  // TTS service
  async textToSpeech(text: string, language: string = 'en') {
    const response = await fetch(`${this.baseUrl}/api/tts/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text,
        language,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`TTS failed: ${response.statusText}`);
    }
    
    return response.blob(); // Returns audio data
  }

  // Health check
  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/api/health`);
    return response.json();
  }

  // Get service info
  async getServiceInfo() {
    const response = await fetch(`${this.baseUrl}/api/info`);
    return response.json();
  }
}

export const apiService = new ApiService();
