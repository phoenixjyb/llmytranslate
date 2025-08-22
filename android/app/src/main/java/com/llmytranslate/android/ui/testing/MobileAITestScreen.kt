package com.llmytranslate.android.ui.testing

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.llmytranslate.android.services.MobileAIService
import com.llmytranslate.android.services.TFLiteLocalService
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject

/**
 * Mobile AI Testing Screen
 * Test TensorFlow Lite GPU performance and functionality
 */

@Composable
fun MobileAITestScreen(
    mobileAIService: MobileAIService
) {
    // Create a simple ViewModel inline for testing
    val context = LocalContext.current
    val viewModel = remember(context) {
        object {
            private val _testResults = MutableStateFlow<List<String>>(emptyList())
            val testResults: StateFlow<List<String>> = _testResults
            
            private val _isInitialized = MutableStateFlow(false)
            val isInitialized: StateFlow<Boolean> = _isInitialized
            
            private val _backendInfo = MutableStateFlow("Backend: Not initialized")
            val backendInfo: StateFlow<String> = _backendInfo
            
            private val coroutineScope = CoroutineScope(Dispatchers.Main + SupervisorJob())
            private val tfliteLocal = TFLiteLocalService(context = context)
            
            fun addTestResult(result: String) {
                val timestamp = System.currentTimeMillis() % 100000
                val formattedResult = "[$timestamp] $result"
                _testResults.value = _testResults.value + formattedResult
            }
            
            fun initializeMobileAI() {
                coroutineScope.launch {
                    addTestResult("🚀 Initializing Mobile AI with bundled assets...")
                    val success = mobileAIService.initializeWithAssets()
                    
                    if (success) {
                        _isInitialized.value = true
                        val info = mobileAIService.getBackendInfo()
                        _backendInfo.value = info
                        addTestResult("✅ Mobile AI initialized successfully")
                        addTestResult("Backend: $info")
                    } else {
                        addTestResult("❌ Mobile AI initialization failed")
                        addTestResult("💡 Note: No .tflite models found in assets, running in fallback mode")
                    }
                }
            }

            fun initializeTFLiteLocal() {
                coroutineScope.launch {
                    addTestResult("🚀 Initializing TFLite(Java) from assets...")
                    val ok = tfliteLocal.initializeFromAssets()
                    if (ok) {
                        addTestResult("✅ TFLite ready: ${tfliteLocal.backendInfo()}")
                    } else {
                        addTestResult("⚠️ No model found; TFLite(Java) demo will run with zeros-only input")
                    }
                }
            }

            fun testTFLiteLocal() {
                coroutineScope.launch {
                    val result = tfliteLocal.runText("hello from android")
                    addTestResult("🧪 TFLite(Java) → ${result.take(100)}${if (result.length > 100) "..." else ""}")
                }
            }
            
            fun testInference() {
                coroutineScope.launch {
                    if (!_isInitialized.value) {
                        addTestResult("⚠️ Please initialize Mobile AI first")
                        return@launch
                    }
                    
                    addTestResult("🧠 Starting inference test...")
                    val startTime = System.currentTimeMillis()
                    
                    val testInput = "Hello, this is a test for mobile AI inference. How are you today?"
                    val result = mobileAIService.processInference(testInput)
                    
                    val duration = System.currentTimeMillis() - startTime
                    addTestResult("⏱️ Inference completed in ${duration}ms")
                    addTestResult("📝 Result: ${result.take(100)}${if (result.length > 100) "..." else ""}")
                }
            }
            
            fun cleanupMobileAI() {
                coroutineScope.launch {
                    addTestResult("🧹 Cleaning up Mobile AI...")
                    mobileAIService.cleanup()
                    _isInitialized.value = false
                    _backendInfo.value = "Backend: Not initialized"
                    addTestResult("✅ Cleanup complete")
                }
            }
            
            fun clearResults() {
                _testResults.value = emptyList()
            }
        }
    }
    val testResults by viewModel.testResults.collectAsState()
    val isInitialized by viewModel.isInitialized.collectAsState()
    val backendInfo by viewModel.backendInfo.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Header
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "🚀 Mobile AI Testing",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "TensorFlow Lite GPU + ONNX Runtime",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = backendInfo,
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                    color = if (isInitialized) Color(0xFF4CAF50) else Color(0xFF9E9E9E)
                )
            }
        }
        
        // Control Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = { viewModel.initializeMobileAI() },
                enabled = !isInitialized,
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Default.PlayArrow, contentDescription = null)
                Spacer(modifier = Modifier.width(4.dp))
                Text("Initialize")
            }
            
            Button(
                onClick = { viewModel.testInference() },
                enabled = isInitialized,
                modifier = Modifier.weight(1f)
            ) {
                Text("Test Inference")
            }
            
            Button(
                onClick = { viewModel.cleanupMobileAI() },
                enabled = isInitialized,
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Default.Stop, contentDescription = null)
                Spacer(modifier = Modifier.width(4.dp))
                Text("Cleanup")
            }
        }
        
        // Utility Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { viewModel.initializeTFLiteLocal() },
                modifier = Modifier.weight(1f)
            ) {
                Text("Init TFLite(Java)")
            }
            OutlinedButton(
                onClick = { viewModel.testTFLiteLocal() },
                modifier = Modifier.weight(1f)
            ) {
                Text("Test TFLite(Java)")
            }
            OutlinedButton(
                onClick = { viewModel.clearResults() },
                modifier = Modifier.weight(1f)
            ) {
                Text("Clear Results")
            }
        }
        
        // Test Results
        Card(
            modifier = Modifier.fillMaxSize()
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                Text(
                    text = "📊 Test Results",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                ) {
                    if (testResults.isEmpty()) {
                        Text(
                            text = "No test results yet. Click 'Initialize' to start.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                            modifier = Modifier.align(Alignment.Center)
                        )
                    } else {
                        Column(
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            testResults.forEach { result ->
                                Text(
                                    text = result,
                                    style = MaterialTheme.typography.bodySmall,
                                    fontFamily = FontFamily.Monospace,
                                    color = when {
                                        result.contains("✅") -> Color(0xFF4CAF50)
                                        result.contains("❌") -> Color(0xFFF44336)
                                        result.contains("⚠️") -> Color(0xFFFF9800)
                                        result.contains("🚀") -> Color(0xFF2196F3)
                                        result.contains("🧠") -> Color(0xFF9C27B0)
                                        result.contains("⏱️") -> Color(0xFF00BCD4)
                                        else -> MaterialTheme.colorScheme.onSurface
                                    }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
