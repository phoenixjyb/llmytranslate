// Shared configuration for both web and React Native platforms
// This ensures identical constants, settings, and data across platforms

export const APP_CONFIG = {
  // API Configuration
  API: {
    BASE_URL: 'http://localhost:8000',
    ENDPOINTS: {
      TRANSLATE: '/api/optimized/translate',
      CHAT: '/api/chat/message',
      TTS: '/api/tts/synthesize',
      VOICE: '/api/voice/message',
      PHONE_START: '/api/phone/start',
      PHONE_END: '/api/phone/end',
      HEALTH: '/api/health',
      INFO: '/api/info',
      CONVERSATIONS: '/api/chat/conversations',
      DETECT_LANGUAGE: '/api/translate/detect',
      LANGUAGES: '/api/translate/languages',
      MODELS: '/api/chat/models',
    },
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3,
  },

  // Services Configuration
  SERVICES: [
    {
      id: 'chat',
      name: 'Chatbot',
      icon: '💬',
      description: 'Intelligent AI conversations with advanced language models and context awareness.',
      features: [
        'Natural language conversations',
        'Context-aware responses',
        'Multiple AI models',
        'Conversation history',
        'Guest & user modes',
      ],
      gradient: {
        start: '#00c6ff',
        end: '#0072ff',
      },
    },
    {
      id: 'translate',
      name: 'Translator',
      icon: '🌐',
      description: 'Professional translation with real-time processing and multiple language support.',
      features: [
        'Multiple language support',
        'Real-time translation',
        'High-quality results',
        'Easy interface',
        'Copy & share results',
      ],
      gradient: {
        start: '#ff006e',
        end: '#8338ec',
      },
    },
    {
      id: 'voice',
      name: 'Voice Chat',
      icon: '🎙️',
      description: 'Natural voice conversations with AI. Speak questions and hear intelligent responses.',
      features: [
        'Speech-to-text with Whisper',
        'Voice conversations',
        'Text-to-speech responses',
        'Text input fallback',
        'Multiple languages',
      ],
      gradient: {
        start: '#7209b7',
        end: '#2d1b69',
      },
    },
    {
      id: 'phone',
      name: 'Phone Call',
      icon: '📞',
      description: 'Real-time phone conversations with AI. Just dial and talk naturally like a phone call!',
      features: [
        'One-click dialing',
        'Real-time conversations',
        'Interrupt anytime',
        'Kid-friendly mode',
        'Call history',
      ],
      gradient: {
        start: '#ff8a00',
        end: '#e52e71',
      },
    },
  ],

  // Language Configuration
  LANGUAGES: [
    { code: 'auto', name: 'Auto Detect', flag: '🌐' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'es', name: 'Spanish', flag: '🇪🇸' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'de', name: 'German', flag: '🇩🇪' },
    { code: 'it', name: 'Italian', flag: '🇮🇹' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'ru', name: 'Russian', flag: '🇷🇺' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
    { code: 'ko', name: 'Korean', flag: '🇰🇷' },
    { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
    { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'th', name: 'Thai', flag: '🇹🇭' },
    { code: 'vi', name: 'Vietnamese', flag: '🇻🇳' },
    { code: 'nl', name: 'Dutch', flag: '🇳🇱' },
    { code: 'sv', name: 'Swedish', flag: '🇸🇪' },
    { code: 'no', name: 'Norwegian', flag: '🇳🇴' },
    { code: 'da', name: 'Danish', flag: '🇩🇰' },
    { code: 'fi', name: 'Finnish', flag: '🇫🇮' },
  ],

  // AI Models Configuration
  MODELS: [
    {
      value: 'gemma3:latest',
      label: 'Gemma3 (Default)',
      description: 'Balanced performance and speed',
      provider: 'Ollama',
      capabilities: ['chat', 'translation'],
    },
    {
      value: 'llama3.1:8b',
      label: 'Llama 3.1 8B',
      description: 'Enhanced reasoning capabilities',
      provider: 'Ollama',
      capabilities: ['chat', 'analysis'],
    },
    {
      value: 'llava:latest',
      label: 'LLaVA (Vision)',
      description: 'Vision and image understanding',
      provider: 'Ollama',
      capabilities: ['chat', 'vision', 'image'],
    },
  ],

  // Design System
  DESIGN: {
    // Color Palette
    colors: {
      primary: {
        chat: { start: '#00c6ff', end: '#0072ff' },
        translate: { start: '#ff006e', end: '#8338ec' },
        voice: { start: '#7209b7', end: '#2d1b69' },
        phone: { start: '#ff8a00', end: '#e52e71' },
        main: { start: '#667eea', end: '#764ba2' },
      },
      status: {
        success: '#4CAF50',
        error: '#F44336',
        warning: '#FF9800',
        info: '#2196F3',
        connecting: '#FF9800',
        connected: '#4CAF50',
        disconnected: '#F44336',
      },
      neutral: {
        white: '#FFFFFF',
        black: '#000000',
        gray100: '#F5F5F5',
        gray200: '#EEEEEE',
        gray300: '#E0E0E0',
        gray400: '#BDBDBD',
        gray500: '#9E9E9E',
        gray600: '#757575',
        gray700: '#616161',
        gray800: '#424242',
        gray900: '#212121',
      },
    },

    // Typography
    typography: {
      sizes: {
        hero: 36,
        title: 28,
        heading: 24,
        subheading: 20,
        body: 16,
        caption: 14,
        small: 12,
        tiny: 10,
      },
      weights: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        heavy: '800',
      },
      lineHeights: {
        tight: 1.2,
        normal: 1.4,
        relaxed: 1.6,
        loose: 1.8,
      },
    },

    // Spacing
    spacing: {
      xs: 4,
      sm: 8,
      md: 16,
      lg: 24,
      xl: 32,
      xxl: 48,
      xxxl: 64,
    },

    // Border Radius
    borderRadius: {
      sm: 4,
      md: 8,
      lg: 12,
      xl: 16,
      xxl: 20,
      round: 9999,
    },

    // Shadows
    shadows: {
      sm: '0 2px 4px rgba(0,0,0,0.1)',
      md: '0 4px 8px rgba(0,0,0,0.12)',
      lg: '0 8px 16px rgba(0,0,0,0.15)',
      xl: '0 12px 24px rgba(0,0,0,0.18)',
      xxl: '0 20px 40px rgba(0,0,0,0.2)',
    },
  },

  // Feature Flags
  FEATURES: {
    VOICE_CHAT: true,
    PHONE_CALL: true,
    FILE_UPLOAD: true,
    CONVERSATION_HISTORY: true,
    MODEL_SELECTION: true,
    LANGUAGE_DETECTION: true,
    REAL_TIME_TRANSLATION: true,
    TTS_ENABLED: true,
    SPEECH_TO_TEXT: true,
    OFFLINE_MODE: false,
    PUSH_NOTIFICATIONS: false,
    ANALYTICS: true,
  },

  // Application Settings
  APP: {
    NAME: 'LLMy Services',
    VERSION: '1.0.0',
    DESCRIPTION: 'AI-powered translation and chat services',
    AUTHOR: 'LLMy Team',
    COPYRIGHT: '© 2025 LLMy Services',
    SUPPORT_EMAIL: 'support@llmy.services',
    PRIVACY_URL: 'https://llmy.services/privacy',
    TERMS_URL: 'https://llmy.services/terms',
  },

  // Performance Settings
  PERFORMANCE: {
    DEBOUNCE_DELAY: 300, // ms
    ANIMATION_DURATION: 300, // ms
    API_TIMEOUT: 30000, // ms
    RETRY_DELAY: 1000, // ms
    MAX_MESSAGE_LENGTH: 10000,
    MAX_TRANSLATION_LENGTH: 5000,
    CONVERSATION_LIMIT: 100,
    MESSAGE_HISTORY_LIMIT: 1000,
  },

  // Platform-specific overrides
  PLATFORM: {
    WEB: {
      STORAGE_PREFIX: 'llmy_web_',
      DEFAULT_THEME: 'light',
    },
    MOBILE: {
      STORAGE_PREFIX: 'llmy_mobile_',
      DEFAULT_THEME: 'auto',
      HAPTIC_FEEDBACK: true,
      STATUS_BAR_STYLE: 'light-content',
    },
  },
};

// Helper functions for accessing configuration
export const getServiceById = (id: string) => {
  return APP_CONFIG.SERVICES.find(service => service.id === id);
};

export const getLanguageByCode = (code: string) => {
  return APP_CONFIG.LANGUAGES.find(lang => lang.code === code);
};

export const getModelByValue = (value: string) => {
  return APP_CONFIG.MODELS.find(model => model.value === value);
};

export const getGradientColors = (serviceId: string) => {
  const service = getServiceById(serviceId);
  return service ? [service.gradient.start, service.gradient.end] : ['#667eea', '#764ba2'];
};

// Environment-specific configuration
export const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Web environment
    return window.location.hostname === 'localhost' 
      ? 'http://localhost:8000' 
      : 'https://api.llmy.services';
  } else {
    // Mobile environment
    return __DEV__ ? 'http://localhost:8000' : 'https://api.llmy.services';
  }
};

// Export individual configs for convenience
export const { SERVICES, LANGUAGES, MODELS, DESIGN, FEATURES, APP, PERFORMANCE } = APP_CONFIG;

export default APP_CONFIG;
