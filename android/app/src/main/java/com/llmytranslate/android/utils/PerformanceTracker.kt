package com.llmytranslate.android.utils

import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.ConcurrentHashMap
import kotlin.system.measureTimeMillis

/**
 * PerformanceTracker tracks timing and performance metrics across the app.
 * Helps identify bottlenecks and lag sources for optimization.
 */
object PerformanceTracker {
    
    private const val TAG = "PerformanceTracker"
    
    // Performance metrics storage
    private val stageTimes = ConcurrentHashMap<String, Long>()
    private val stageStartTimes = ConcurrentHashMap<String, Long>()
    private val operationCounts = ConcurrentHashMap<String, Int>()
    
    // Performance state for UI display
    private val _performanceData = MutableStateFlow(PerformanceData())
    val performanceData: StateFlow<PerformanceData> = _performanceData.asStateFlow()
    
    /**
     * Start timing a specific stage/operation.
     */
    fun startStage(stageName: String) {
        val currentTime = System.currentTimeMillis()
        stageStartTimes[stageName] = currentTime
        Log.d(TAG, "⏱️ Started: $stageName at ${currentTime}")
    }
    
    /**
     * End timing a stage and log the duration.
     */
    fun endStage(stageName: String): Long {
        val endTime = System.currentTimeMillis()
        val startTime = stageStartTimes[stageName] ?: endTime
        val duration = endTime - startTime
        
        stageTimes[stageName] = duration
        operationCounts[stageName] = (operationCounts[stageName] ?: 0) + 1
        
        Log.i(TAG, "✅ Completed: $stageName in ${duration}ms")
        
        // Update performance data
        updatePerformanceData()
        
        return duration
    }
    
    /**
     * Measure the time taken by a block of code.
     */
    fun <T> measureStage(stageName: String, block: () -> T): T {
        var result: T
        val duration = measureTimeMillis {
            result = block()
        }
        
        stageTimes[stageName] = duration
        operationCounts[stageName] = (operationCounts[stageName] ?: 0) + 1
        
        Log.i(TAG, "📊 Measured: $stageName took ${duration}ms")
        updatePerformanceData()
        
        return result
    }
    
    /**
     * Log application startup timing.
     */
    fun logAppStartup(stage: AppStartupStage) {
        when (stage) {
            AppStartupStage.APPLICATION_CREATE -> startStage("app_startup")
            AppStartupStage.ACTIVITY_CREATE -> {
                endStage("app_startup")
                startStage("activity_create")
            }
            AppStartupStage.COMPOSE_INIT -> {
                endStage("activity_create")
                startStage("compose_init")
            }
            AppStartupStage.NAVIGATION_READY -> {
                endStage("compose_init")
                startStage("navigation_setup")
            }
            AppStartupStage.SERVICES_INIT -> {
                endStage("navigation_setup")
                startStage("services_init")
            }
            AppStartupStage.UI_READY -> {
                endStage("services_init")
                Log.i(TAG, "🚀 App fully loaded!")
            }
        }
    }
    
    /**
     * Log network operation timing.
     */
    fun logNetworkOperation(operation: NetworkOperation, duration: Long) {
        val operationName = when (operation) {
            NetworkOperation.SERVER_DISCOVERY -> "network_discovery"
            NetworkOperation.WEBSOCKET_CONNECT -> "websocket_connect"
            NetworkOperation.WEBSOCKET_DISCONNECT -> "websocket_disconnect"
            NetworkOperation.MESSAGE_SEND -> "message_send"
            NetworkOperation.MESSAGE_RECEIVE -> "message_receive"
            NetworkOperation.SESSION_START -> "session_start"
            NetworkOperation.SETTINGS_UPDATE -> "settings_update"
        }
        
        stageTimes[operationName] = duration
        operationCounts[operationName] = (operationCounts[operationName] ?: 0) + 1
        
        Log.i(TAG, "🌐 Network: $operationName took ${duration}ms")
        updatePerformanceData()
    }
    
    /**
     * Log audio operation timing.
     */
    fun logAudioOperation(operation: AudioOperation, duration: Long) {
        val operationName = when (operation) {
            AudioOperation.STT_INIT -> "stt_init"
            AudioOperation.STT_START -> "stt_start"
            AudioOperation.STT_RESULT -> "stt_result"
            AudioOperation.TTS_INIT -> "tts_init"
            AudioOperation.TTS_SPEAK -> "tts_speak"
            AudioOperation.TTS_COMPLETE -> "tts_complete"
        }
        
        stageTimes[operationName] = duration
        operationCounts[operationName] = (operationCounts[operationName] ?: 0) + 1
        
        Log.i(TAG, "🎤 Audio: $operationName took ${duration}ms")
        updatePerformanceData()
    }
    
    /**
     * Log UI operation timing.
     */
    fun logUIOperation(operation: UIOperation, duration: Long) {
        val operationName = when (operation) {
            UIOperation.SCREEN_LOAD -> "screen_load"
            UIOperation.COMPOSE_RECOMPOSITION -> "compose_recomposition"
            UIOperation.LIST_SCROLL -> "list_scroll"
            UIOperation.INPUT_PROCESSING -> "input_processing"
            UIOperation.NAVIGATION -> "navigation"
        }
        
        stageTimes[operationName] = duration
        operationCounts[operationName] = (operationCounts[operationName] ?: 0) + 1
        
        Log.i(TAG, "🎨 UI: $operationName took ${duration}ms")
        updatePerformanceData()
    }
    
    /**
     * Get performance summary for debugging.
     */
    fun getPerformanceSummary(): String {
        return buildString {
            appendLine("📊 Performance Summary:")
            appendLine("========================")
            
            stageTimes.toSortedMap().forEach { (stage, duration) ->
                val count = operationCounts[stage] ?: 1
                val avgDuration = duration / count
                appendLine("$stage: ${duration}ms (avg: ${avgDuration}ms, count: $count)")
            }
            
            appendLine("========================")
            appendLine("Total operations: ${operationCounts.values.sum()}")
        }
    }
    
    /**
     * Log memory usage.
     */
    fun logMemoryUsage(context: String = "") {
        val runtime = Runtime.getRuntime()
        val usedMemory = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024
        val totalMemory = runtime.totalMemory() / 1024 / 1024
        val maxMemory = runtime.maxMemory() / 1024 / 1024
        
        Log.i(TAG, "💾 Memory $context: Used ${usedMemory}MB / Total ${totalMemory}MB / Max ${maxMemory}MB")
    }
    
    /**
     * Clear all performance data.
     */
    fun clear() {
        stageTimes.clear()
        stageStartTimes.clear()
        operationCounts.clear()
        updatePerformanceData()
        Log.i(TAG, "🧹 Performance data cleared")
    }
    
    /**
     * Update the performance data state flow.
     */
    private fun updatePerformanceData() {
        val data = PerformanceData(
            stageTimes = stageTimes.toMap(),
            operationCounts = operationCounts.toMap(),
            lastUpdate = System.currentTimeMillis()
        )
        _performanceData.value = data
    }
}

/**
 * Data class holding performance metrics.
 */
data class PerformanceData(
    val stageTimes: Map<String, Long> = emptyMap(),
    val operationCounts: Map<String, Int> = emptyMap(),
    val lastUpdate: Long = 0L
) {
    fun getAverageTime(operation: String): Long {
        val totalTime = stageTimes[operation] ?: 0L
        val count = operationCounts[operation] ?: 1
        return totalTime / count
    }
    
    fun getTotalOperations(): Int = operationCounts.values.sum()
    
    fun getSlowestOperation(): Pair<String, Long>? {
        return stageTimes.maxByOrNull { it.value }?.toPair()
    }
}

/**
 * Application startup stages for timing.
 */
enum class AppStartupStage {
    APPLICATION_CREATE,
    ACTIVITY_CREATE,
    COMPOSE_INIT,
    NAVIGATION_READY,
    SERVICES_INIT,
    UI_READY
}

/**
 * Network operation types for timing.
 */
enum class NetworkOperation {
    SERVER_DISCOVERY,
    WEBSOCKET_CONNECT,
    WEBSOCKET_DISCONNECT,
    MESSAGE_SEND,
    MESSAGE_RECEIVE,
    SESSION_START,
    SETTINGS_UPDATE
}

/**
 * Audio operation types for timing.
 */
enum class AudioOperation {
    STT_INIT,
    STT_START,
    STT_RESULT,
    TTS_INIT,
    TTS_SPEAK,
    TTS_COMPLETE
}

/**
 * UI operation types for timing.
 */
enum class UIOperation {
    SCREEN_LOAD,
    COMPOSE_RECOMPOSITION,
    LIST_SCROLL,
    INPUT_PROCESSING,
    NAVIGATION
}
