package com.llmytranslate.android.utils

import android.util.Log

/**
 * Centralized logger for connection-related events to help with logcat debugging.
 * All connection events are logged with specific tags for easy filtering.
 */
object ConnectionLogger {
    private const val BASE_TAG = "LLMyTranslate_Connection"
    
    // Specific tags for different components
    private const val TERMUX_TAG = "${BASE_TAG}_Termux"
    private const val HEALTH_TAG = "${BASE_TAG}_Health"
    private const val RETRY_TAG = "${BASE_TAG}_Retry"
    private const val FALLBACK_TAG = "${BASE_TAG}_Fallback"
    private const val DIAGNOSTIC_TAG = "${BASE_TAG}_Diagnostic"
    
    /**
     * Log Termux connection attempts and results.
     */
    fun logTermuxConnection(
        action: String,
        success: Boolean,
        latencyMs: Long? = null,
        error: String? = null,
        attempt: Int? = null
    ) {
        val message = buildString {
            append("[$action] ")
            if (attempt != null) append("Attempt $attempt: ")
            append(if (success) "✅ SUCCESS" else "❌ FAILED")
            latencyMs?.let { append(" (${it}ms)") }
            error?.let { append(" - $it") }
        }
        
        if (success) {
            Log.i(TERMUX_TAG, message)
        } else {
            Log.w(TERMUX_TAG, message)
        }
    }
    
    /**
     * Log connection health monitoring events.
     */
    fun logHealthMonitoring(
        successRate: Double,
        avgLatency: Long,
        consecutiveFailures: Int,
        recommendedTimeout: Long,
        recommendedRetries: Int
    ) {
        val healthStatus = when {
            successRate >= 0.8 -> "EXCELLENT"
            successRate >= 0.6 -> "GOOD"
            successRate >= 0.4 -> "POOR"
            else -> "CRITICAL"
        }
        
        val message = "Health: $healthStatus | Success: ${(successRate * 100).toInt()}% | " +
                     "Avg Latency: ${avgLatency}ms | Consecutive Failures: $consecutiveFailures | " +
                     "Recommended: ${recommendedTimeout}ms timeout, $recommendedRetries retries"
        
        when (healthStatus) {
            "EXCELLENT", "GOOD" -> Log.i(HEALTH_TAG, message)
            "POOR" -> Log.w(HEALTH_TAG, message)
            "CRITICAL" -> Log.e(HEALTH_TAG, message)
        }
    }
    
    /**
     * Log retry strategy decisions.
     */
    fun logRetryStrategy(
        attempt: Int,
        maxRetries: Int,
        delayMs: Long,
        timeoutMs: Long,
        reason: String
    ) {
        val message = "Retry $attempt/$maxRetries: delay=${delayMs}ms, timeout=${timeoutMs}ms - $reason"
        Log.d(RETRY_TAG, message)
    }
    
    /**
     * Log fallback decisions and actions.
     */
    fun logFallback(
        trigger: String,
        fallbackType: String,
        success: Boolean,
        latencyMs: Long? = null
    ) {
        val message = buildString {
            append("[$trigger] Fallback to $fallbackType: ")
            append(if (success) "✅ SUCCESS" else "❌ FAILED")
            latencyMs?.let { append(" (${it}ms)") }
        }
        
        if (success) {
            Log.i(FALLBACK_TAG, message)
        } else {
            Log.e(FALLBACK_TAG, message)
        }
    }
    
    /**
     * Log diagnostic information for debugging.
     */
    fun logDiagnostic(component: String, info: String) {
        Log.d(DIAGNOSTIC_TAG, "[$component] $info")
    }
    
    /**
     * Log summary of connection session for analysis.
     */
    fun logSessionSummary(
        totalAttempts: Int,
        successfulAttempts: Int,
        avgLatency: Long,
        fallbackUsed: Boolean,
        sessionDurationMs: Long
    ) {
        val successRate = if (totalAttempts > 0) successfulAttempts.toDouble() / totalAttempts else 0.0
        
        val message = "SESSION SUMMARY: " +
                     "Attempts: $successfulAttempts/$totalAttempts (${(successRate * 100).toInt()}%) | " +
                     "Avg Latency: ${avgLatency}ms | " +
                     "Fallback Used: $fallbackUsed | " +
                     "Duration: ${sessionDurationMs}ms"
        
        Log.i(BASE_TAG, message)
    }
    
    /**
     * Create a logcat filter command for easy debugging.
     */
    fun getLogcatFilterCommand(): String {
        return "adb logcat -s $BASE_TAG:* $TERMUX_TAG:* $HEALTH_TAG:* $RETRY_TAG:* $FALLBACK_TAG:* $DIAGNOSTIC_TAG:*"
    }
    
    /**
     * Print instructions for logcat debugging.
     */
    fun printLogcatInstructions() {
        Log.i(BASE_TAG, "=== LOGCAT DEBUGGING INSTRUCTIONS ===")
        Log.i(BASE_TAG, "To monitor connection logs, use:")
        Log.i(BASE_TAG, getLogcatFilterCommand())
        Log.i(BASE_TAG, "Or filter by specific components:")
        Log.i(BASE_TAG, "  Termux: adb logcat -s $TERMUX_TAG:*")
        Log.i(BASE_TAG, "  Health: adb logcat -s $HEALTH_TAG:*")
        Log.i(BASE_TAG, "  Retry:  adb logcat -s $RETRY_TAG:*")
        Log.i(BASE_TAG, "=====================================")
    }
}
