package com.llmytranslate.android.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.llmytranslate.android.models.*
import com.llmytranslate.android.services.STTService
import com.llmytranslate.android.services.TTSService
import com.llmytranslate.android.services.WebSocketService
import com.llmytranslate.android.utils.NetworkManager
import com.llmytranslate.android.utils.ServerDiscoveryResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * MainViewModel manages the overall application state and coordinates services.
 */
@HiltViewModel
class MainViewModel @Inject constructor(
    private val networkManager: NetworkManager,
    private val sttService: STTService,
    private val ttsService: TTSService
) : ViewModel() {
    
    // Application state
    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()
    
    // Server discovery
    private val _discoveredServers = MutableStateFlow<List<ServerDiscoveryResult>>(emptyList())
    val discoveredServers: StateFlow<List<ServerDiscoveryResult>> = _discoveredServers.asStateFlow()
    
    // Connection state
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    // WebSocket service reference (will be injected when service is bound)
    private var webSocketService: WebSocketService? = null
    
    init {
        initializeServices()
        discoverServers()
    }
    
    /**
     * Initialize core services.
     */
    private fun initializeServices() {
        viewModelScope.launch {
            // Initialize STT service
            sttService.initialize()
            
            // Initialize TTS service
            ttsService.initialize()
            
            _uiState.value = _uiState.value.copy(isInitialized = true)
        }
    }
    
    /**
     * Discover LLMyTranslate servers on the network.
     */
    fun discoverServers() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                connectionState = ConnectionState.CONNECTING
            )
            
            try {
                val servers = networkManager.discoverServers()
                _discoveredServers.value = servers
                
                if (servers.isNotEmpty()) {
                    val bestServer = servers.minByOrNull { it.responseTime }
                    bestServer?.let { server ->
                        _uiState.value = _uiState.value.copy(
                            serverInfo = server.serverInfo,
                            connectionState = ConnectionState.DISCONNECTED
                        )
                    }
                } else {
                    _uiState.value = _uiState.value.copy(
                        connectionState = ConnectionState.ERROR
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    connectionState = ConnectionState.ERROR
                )
            }
        }
    }
    
    /**
     * Connect to a specific server.
     */
    fun connectToServer(server: ServerDiscoveryResult) {
        viewModelScope.launch {
            webSocketService?.let { service ->
                val sessionSettings = SessionSettings(
                    language = "en-US",
                    kidFriendly = false,
                    model = "gemma2:2b",
                    useNativeSTT = true,
                    useNativeTTS = true
                )
                
                service.connect(server.websocketUrl, sessionSettings)
                
                // Update UI state
                _uiState.value = _uiState.value.copy(
                    connectionState = ConnectionState.CONNECTING,
                    serverInfo = server.serverInfo
                )
            }
        }
    }
    
    /**
     * Set WebSocket service reference (called when service is bound).
     */
    fun setWebSocketService(service: WebSocketService) {
        webSocketService = service
        
        // Observe WebSocket connection state
        viewModelScope.launch {
            service.connectionState.collect { state ->
                _connectionState.value = state
                _uiState.value = _uiState.value.copy(connectionState = state)
            }
        }
        
        // Observe server info updates
        viewModelScope.launch {
            service.serverInfo.collect { serverInfo ->
                serverInfo?.let {
                    _uiState.value = _uiState.value.copy(serverInfo = it)
                }
            }
        }
    }
    
    /**
     * Disconnect from current server.
     */
    fun disconnect() {
        webSocketService?.disconnect()
        _uiState.value = _uiState.value.copy(
            connectionState = ConnectionState.DISCONNECTED,
            currentSessionId = null
        )
    }
    
    /**
     * Get current network status.
     */
    fun getNetworkStatus(): NetworkStatus {
        return NetworkStatus(
            isConnected = networkManager.hasInternetConnection(),
            isWiFi = networkManager.isWiFiConnected(),
            hasInternet = networkManager.hasInternetConnection(),
            wifiName = networkManager.getCurrentWiFiName()
        )
    }
    
    /**
     * Get STT service capabilities.
     */
    fun getSTTCapabilities(): STTCapabilities {
        return STTCapabilities(
            isAvailable = true, // Android STT is always available
            supportsOffline = sttService.supportsOfflineRecognition(),
            availableLanguages = sttService.getAvailableLanguages(),
            supportsContinuous = true,
            supportsPartialResults = true
        )
    }
    
    /**
     * Get TTS service capabilities.
     */
    fun getTTSCapabilities(): TTSCapabilities {
        return TTSCapabilities(
            isAvailable = ttsService.isInitializedState.value,
            supportsOffline = true, // Android TTS is always offline
            supportsSamsungNeural = ttsService.supportsSamsungNeural(),
            availableLanguages = ttsService.getSupportedLanguages(),
            supportsSSML = true
        )
    }
    
    override fun onCleared() {
        super.onCleared()
        webSocketService?.disconnect()
        sttService.destroy()
        ttsService.destroy()
    }
}

// Capability data classes
data class STTCapabilities(
    val isAvailable: Boolean,
    val supportsOffline: Boolean,
    val availableLanguages: List<String>,
    val supportsContinuous: Boolean,
    val supportsPartialResults: Boolean
)

data class TTSCapabilities(
    val isAvailable: Boolean,
    val supportsOffline: Boolean,
    val supportsSamsungNeural: Boolean,
    val availableLanguages: List<String>,
    val supportsSSML: Boolean
)
