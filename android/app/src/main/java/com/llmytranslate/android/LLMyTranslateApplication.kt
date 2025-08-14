package com.llmytranslate.android

import android.app.Application
import android.util.Log
import com.llmytranslate.android.utils.PerformanceTracker
import com.llmytranslate.android.utils.AppStartupStage
import dagger.hilt.android.HiltAndroidApp

/**
 * Main Application class for LLMyTranslate Android app.
 */
@HiltAndroidApp
class LLMyTranslateApplication : Application() {
    
    companion object {
        private const val TAG = "LLMyTranslateApp"
    }
    
    override fun onCreate() {
        // Start timing app startup
        PerformanceTracker.logAppStartup(AppStartupStage.APPLICATION_CREATE)
        PerformanceTracker.logMemoryUsage("App onCreate start")
        
        super.onCreate()
        
        Log.i(TAG, "🚀 LLMyTranslate Application starting...")
        
        // Initialize any global components here
        initializeGlobalComponents()
        
        PerformanceTracker.logMemoryUsage("App onCreate complete")
        Log.i(TAG, "✅ LLMyTranslate Application created")
    }
    
    private fun initializeGlobalComponents() {
        PerformanceTracker.measureStage("global_components_init") {
            // Initialize crash reporting, analytics, etc.
            // For now, just log the initialization
            Log.d(TAG, "Initializing global components...")
        }
    }
}
