package com.llmytranslate.android

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Main Application class for LLMyTranslate Android app.
 */
@HiltAndroidApp
class LLMyTranslateApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize any global components here
        // For example: logging, crash reporting, etc.
    }
}
