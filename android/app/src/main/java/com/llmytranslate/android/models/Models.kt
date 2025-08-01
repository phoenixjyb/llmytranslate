package com.llmytranslate.android.models

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import java.util.Date

/**
 * Data models for LLMyTranslate Android app.
 */

@JsonClass(generateAdapter = true)
data class ServerInfo(
    @Json(name = "service_name") val serviceName: String,
    @Json(name = "service_type") val serviceType: String,
    val version: String,
    @Json(name = "websocket_endpoint") val websocketEndpoint: String,
    val capabilities: ServerCapabilities,
    val models: List<String>,
    val languages: List<String>
)

@JsonClass(generateAdapter = true)
data class ServerCapabilities(
    @Json(name = "text_chat") val textChat: Boolean,
    @Json(name = "voice_chat") val voiceChat: Boolean,
    val translation: Boolean,
    @Json(name = "kid_friendly") val kidFriendly: Boolean,
    @Json(name = "native_stt_supported") val nativeSTTSupported: Boolean,
    @Json(name = "native_tts_supported") val nativeTTSSupported: Boolean
)

@Entity(tableName = "messages")
data class Message(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val sessionId: String,
    val content: String,
    val isFromUser: Boolean,
    val timestamp: Date,
    val processingTime: Float? = null
)

@Entity(tableName = "chat_sessions")
data class ChatSession(
    @PrimaryKey
    val sessionId: String,
    val startTime: Date,
    val endTime: Date? = null,
    val messageCount: Int = 0,
    val sessionType: SessionType,
    val settings: SessionSettings
)

enum class SessionType {
    TEXT_CHAT,
    VOICE_CHAT,
    TRANSLATION
}

@JsonClass(generateAdapter = true)
data class SessionSettings(
    val language: String = "en-US",
    @Json(name = "kid_friendly") val kidFriendly: Boolean = false,
    val model: String = "gemma2:2b",
    @Json(name = "use_native_stt") val useNativeSTT: Boolean = true,
    @Json(name = "use_native_tts") val useNativeTTS: Boolean = true,
    val voiceSpeed: Float = 1.0f
)

@Entity(tableName = "app_settings")
data class AppSettings(
    @PrimaryKey
    val id: Int = 1,
    val serverAddress: String? = null,
    val autoDiscoverServer: Boolean = true,
    val autoConnect: Boolean = true,
    val defaultLanguage: String = "en-US",
    val defaultVoiceSpeed: Float = 1.0f,
    val kidFriendlyMode: Boolean = false,
    val saveConversationHistory: Boolean = true,
    val useNativeSTT: Boolean = true,
    val useNativeTTS: Boolean = true
)

// WebSocket message types
@JsonClass(generateAdapter = true)
data class WebSocketMessage(
    val type: String,
    @Json(name = "session_id") val sessionId: String? = null,
    val text: String? = null,
    val settings: SessionSettings? = null,
    val message: String? = null,
    @Json(name = "server_info") val serverInfo: ServerInfo? = null,
    val timing: ProcessingTiming? = null,
    @Json(name = "use_native_tts") val useNativeTTS: Boolean? = null,
    @Json(name = "original_text") val originalText: String? = null
)

@JsonClass(generateAdapter = true)
data class ProcessingTiming(
    @Json(name = "llm_processing") val llmProcessing: Float? = null,
    @Json(name = "total_processing") val totalProcessing: Float? = null
)

// Connection states
enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    ERROR
}

// Audio states
enum class AudioState {
    IDLE,
    LISTENING,
    PROCESSING,
    SPEAKING
}

// UI State models
data class ChatUiState(
    val messages: List<Message> = emptyList(),
    val isLoading: Boolean = false,
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val currentInput: String = "",
    val errorMessage: String? = null
)

data class VoiceUiState(
    val audioState: AudioState = AudioState.IDLE,
    val isRecording: Boolean = false,
    val isSpeaking: Boolean = false,
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val currentTranscription: String = "",
    val errorMessage: String? = null
)

data class SettingsUiState(
    val settings: AppSettings = AppSettings(),
    val serverInfo: ServerInfo? = null,
    val isConnected: Boolean = false,
    val availableLanguages: List<String> = emptyList(),
    val availableModels: List<String> = emptyList()
)

data class MainUiState(
    val connectionState: ConnectionState = ConnectionState.DISCONNECTED,
    val serverInfo: ServerInfo? = null,
    val currentSessionId: String? = null,
    val isInitialized: Boolean = false
)
