package com.llmytranslate.android.utils

import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

/**
 * Monitor for tracking Termux Ollama connection health and reliability.
 * Detects when connections become intermittent and adjusts retry strategies.
 */
class TermuxConnectionMonitor {
    
    companion object {
        private const val TAG = "TermuxConnectionMonitor"
        private const val HEALTH_CHECK_INTERVAL_MS = 30000L // 30 seconds
        private const val FAILURE_THRESHOLD = 3 // Consider unhealthy after 3 failures
        private const val SUCCESS_THRESHOLD = 2 // Consider healthy after 2 successes
    }
    
    data class ConnectionHealth(
        val isHealthy: Boolean,
        val consecutiveFailures: Int,
        val consecutiveSuccesses: Int,
        val totalAttempts: Int,
        val successRate: Float,
        val averageLatencyMs: Long,
        val lastErrorMessage: String,
        val recommendedAction: String
    )
    
    private val consecutiveFailures = AtomicInteger(0)
    private val consecutiveSuccesses = AtomicInteger(0)
    private val totalAttempts = AtomicInteger(0)
    private val totalSuccesses = AtomicInteger(0)
    private val totalLatency = AtomicLong(0)
    private var lastErrorMessage = ""
    
    private val _healthState = MutableStateFlow(
        ConnectionHealth(
            isHealthy = true,
            consecutiveFailures = 0,
            consecutiveSuccesses = 0,
            totalAttempts = 0,
            successRate = 1.0f,
            averageLatencyMs = 0,
            lastErrorMessage = "",
            recommendedAction = "Connection appears stable"
        )
    )
    val healthState: StateFlow<ConnectionHealth> = _healthState.asStateFlow()
    
    /**
     * Record a successful connection attempt.
     */
    fun recordSuccess(latencyMs: Long) {
        consecutiveFailures.set(0)
        consecutiveSuccesses.incrementAndGet()
        totalAttempts.incrementAndGet()
        totalSuccesses.incrementAndGet()
        totalLatency.addAndGet(latencyMs)
        
        updateHealthState()
        
        Log.d(TAG, "Success recorded: ${latencyMs}ms latency, ${consecutiveSuccesses.get()} consecutive successes")
    }
    
    /**
     * Record a failed connection attempt.
     */
    fun recordFailure(errorMessage: String) {
        consecutiveSuccesses.set(0)
        consecutiveFailures.incrementAndGet()
        totalAttempts.incrementAndGet()
        lastErrorMessage = errorMessage
        
        updateHealthState()
        
        val failures = consecutiveFailures.get()
        Log.w(TAG, "Failure recorded: $errorMessage ($failures consecutive failures)")
        
        if (failures >= FAILURE_THRESHOLD) {
            Log.e(TAG, "Connection marked as unhealthy after $failures consecutive failures")
        }
    }
    
    private fun updateHealthState() {
        val attempts = totalAttempts.get()
        val successes = totalSuccesses.get()
        val failures = consecutiveFailures.get()
        val successStreak = consecutiveSuccesses.get()
        
        val successRate = if (attempts > 0) successes.toFloat() / attempts else 1.0f
        val avgLatency = if (successes > 0) totalLatency.get() / successes else 0L
        val isHealthy = failures < FAILURE_THRESHOLD || successStreak >= SUCCESS_THRESHOLD
        
        val recommendedAction = when {
            failures >= FAILURE_THRESHOLD * 2 -> "Consider restarting Ollama in Termux"
            failures >= FAILURE_THRESHOLD -> "Connection unstable - using extended timeouts"
            successRate < 0.5f && attempts > 5 -> "Poor success rate - check network stability"
            avgLatency > 10000 -> "High latency detected - check Termux performance"
            else -> "Connection appears stable"
        }
        
        // Log health monitoring information for logcat debugging
        if (attempts > 0) { // Only log if we have data
            ConnectionLogger.logHealthMonitoring(
                successRate.toDouble(),
                avgLatency,
                failures,
                getRecommendedTimeout(),
                getRecommendedRetries()
            )
        }
        
        _healthState.value = ConnectionHealth(
            isHealthy = isHealthy,
            consecutiveFailures = failures,
            consecutiveSuccesses = successStreak,
            totalAttempts = attempts,
            successRate = successRate,
            averageLatencyMs = avgLatency,
            lastErrorMessage = lastErrorMessage,
            recommendedAction = recommendedAction
        )
    }
    
    /**
     * Get recommended timeout based on connection health.
     */
    fun getRecommendedTimeout(): Long {
        val health = _healthState.value
        return when {
            health.consecutiveFailures >= FAILURE_THRESHOLD -> 45000L // 45 seconds for unstable
            health.averageLatencyMs > 8000 -> 30000L // 30 seconds for slow
            health.successRate < 0.7f -> 25000L // 25 seconds for unreliable
            else -> 15000L // 15 seconds for stable
        }
    }
    
    /**
     * Get recommended retry count based on connection health.
     */
    fun getRecommendedRetries(): Int {
        val health = _healthState.value
        return when {
            health.consecutiveFailures >= FAILURE_THRESHOLD -> 5 // More retries for unstable
            health.successRate < 0.5f -> 4 // Extra retries for unreliable
            else -> 3 // Normal retries for stable
        }
    }
    
    /**
     * Check if we should use fallback mode immediately.
     */
    fun shouldSkipNativeMode(): Boolean {
        val health = _healthState.value
        return health.consecutiveFailures >= FAILURE_THRESHOLD * 2 && 
               health.successRate < 0.3f &&
               health.totalAttempts > 10
    }
    
    /**
     * Reset health statistics (useful after Ollama restart).
     */
    fun reset() {
        consecutiveFailures.set(0)
        consecutiveSuccesses.set(0)
        totalAttempts.set(0)
        totalSuccesses.set(0)
        totalLatency.set(0)
        lastErrorMessage = ""
        
        updateHealthState()
        Log.i(TAG, "Connection health statistics reset")
    }
    
    /**
     * Get a human-readable health summary.
     */
    fun getHealthSummary(): String {
        val health = _healthState.value
        return buildString {
            appendLine("🔍 Termux Connection Health:")
            appendLine("   Status: ${if (health.isHealthy) "✅ Healthy" else "❌ Unhealthy"}")
            appendLine("   Success Rate: ${(health.successRate * 100).toInt()}% (${totalSuccesses.get()}/${health.totalAttempts})")
            appendLine("   Average Latency: ${health.averageLatencyMs}ms")
            appendLine("   Consecutive Failures: ${health.consecutiveFailures}")
            appendLine("   Consecutive Successes: ${health.consecutiveSuccesses}")
            if (health.lastErrorMessage.isNotEmpty()) {
                appendLine("   Last Error: ${health.lastErrorMessage}")
            }
            appendLine("   Recommendation: ${health.recommendedAction}")
        }
    }
}
