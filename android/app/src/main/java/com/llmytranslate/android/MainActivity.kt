package com.llmytranslate.android

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.core.content.ContextCompat
import androidx.navigation.compose.rememberNavController
import com.llmytranslate.android.ui.navigation.AppNavigation
import com.llmytranslate.android.ui.theme.LLMyTranslateTheme
import com.llmytranslate.android.utils.PerformanceTracker
import com.llmytranslate.android.utils.AppStartupStage

/**
 * Main Activity for LLMyTranslate Android app.
 * Uses Jetpack Compose for modern UI with Material Design 3.
 */
class MainActivity : ComponentActivity() {
    
    companion object {
        private const val TAG = "MainActivity"
        private const val RECORD_AUDIO_PERMISSION = Manifest.permission.RECORD_AUDIO
    }
    
    // Permission launcher for audio recording
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            Log.i(TAG, "✅ Audio recording permission granted")
            initializeSTTService()
        } else {
            Log.w(TAG, "❌ Audio recording permission denied")
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        PerformanceTracker.logAppStartup(AppStartupStage.ACTIVITY_CREATE)
        PerformanceTracker.logMemoryUsage("MainActivity onCreate start")
        
        super.onCreate(savedInstanceState)
        
        Log.i(TAG, "🎨 Setting up Compose UI...")
        
        val composeSetupTime = PerformanceTracker.measureStage("compose_setup") {
            setContent {
                PerformanceTracker.logAppStartup(AppStartupStage.COMPOSE_INIT)
                
                LLMyTranslateTheme {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.background
                    ) {
                        LLMyTranslateApp()
                    }
                }
            }
        }
        
        // Check and request audio permission
        checkAudioPermission()
        
        PerformanceTracker.logMemoryUsage("MainActivity onCreate complete")
        Log.i(TAG, "✅ MainActivity created in ${composeSetupTime}ms")
    }
    
    private fun checkAudioPermission() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                RECORD_AUDIO_PERMISSION
            ) == PackageManager.PERMISSION_GRANTED -> {
                Log.i(TAG, "✅ Audio permission already granted")
                initializeSTTService()
            }
            else -> {
                Log.i(TAG, "🔒 Requesting audio recording permission...")
                requestPermissionLauncher.launch(RECORD_AUDIO_PERMISSION)
            }
        }
    }
    
    private fun initializeSTTService() {
        val initTime = kotlin.system.measureTimeMillis {
            // Initialize STT service if available
            Log.i(TAG, "🎤 STT Service initialized after permission grant")
        }
        Log.d(TAG, "📊 STT initialization took ${initTime}ms")
    }
    
    override fun onStart() {
        super.onStart()
        PerformanceTracker.measureStage("activity_start") {
            Log.d(TAG, "Activity starting...")
        }
    }
    
    override fun onResume() {
        super.onResume()
        PerformanceTracker.measureStage("activity_resume") {
            Log.d(TAG, "Activity resuming...")
            PerformanceTracker.logMemoryUsage("Activity resumed")
        }
    }
}

@Composable
fun LLMyTranslateApp() {
    PerformanceTracker.logAppStartup(AppStartupStage.NAVIGATION_READY)
    
    val navController = rememberNavController()
    
    AppNavigation(navController = navController)
    
    PerformanceTracker.logAppStartup(AppStartupStage.UI_READY)
}

@Preview(showBackground = true)
@Composable
fun LLMyTranslateAppPreview() {
    LLMyTranslateTheme {
        LLMyTranslateApp()
    }
}
