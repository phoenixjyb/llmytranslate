package com.llmytranslate.android.utils

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

/**
 * Debug utilities for Termux connection troubleshooting.
 */
object TermuxDebugger {
    private const val TAG = "TermuxDebugger"
    
    // Different localhost variations to test
    private val LOCALHOST_VARIATIONS = listOf(
        "127.0.0.1",
        "localhost", 
        "10.0.2.2", // Android Emulator host
        "192.168.1.1", // Common router IP
    )
    
    private val COMMON_PORTS = listOf(11434, 8000, 8080)
    
    suspend fun debugTermuxConnection(context: Context): String = withContext(Dispatchers.IO) {
        val results = mutableListOf<String>()
        
        results.add("🔍 TERMUX CONNECTION DEBUG")
        results.add("========================================")
        
        // Test network permissions
        results.add("\n📱 Network Permissions:")
        val hasInternet = context.checkSelfPermission(android.Manifest.permission.INTERNET) == android.content.pm.PackageManager.PERMISSION_GRANTED
        results.add("   INTERNET: ${if (hasInternet) "✅ GRANTED" else "❌ DENIED"}")
        
        // Test each localhost variation
        results.add("\n🌐 Testing Localhost Variations:")
        
        for (host in LOCALHOST_VARIATIONS) {
            for (port in COMMON_PORTS) {
                val url = "http://$host:$port"
                val result = testHttpConnection(url)
                results.add("   $url: $result")
            }
        }
        
        // Test specific Ollama endpoints
        results.add("\n🤖 Testing Ollama Endpoints:")
        for (host in LOCALHOST_VARIATIONS) {
            val ollamaUrl = "http://$host:11434"
            results.add("   $ollamaUrl/api/version: ${testOllamaVersion(ollamaUrl)}")
            results.add("   $ollamaUrl/api/tags: ${testOllamaTags(ollamaUrl)}")
        }
        
        // Test if we can reach any web services
        results.add("\n🔗 External Connectivity Test:")
        results.add("   Google DNS: ${testHttpConnection("http://8.8.8.8")}")
        results.add("   httpbin.org: ${testHttpConnection("http://httpbin.org/get")}")
        
        results.joinToString("\n")
    }
    
    private suspend fun testHttpConnection(url: String): String = withContext(Dispatchers.IO) {
        try {
            val connection = URL(url).openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            connection.requestMethod = "GET"
            
            val responseCode = connection.responseCode
            when (responseCode) {
                200 -> "✅ SUCCESS (HTTP 200)"
                404 -> "⚠️ NOT FOUND (HTTP 404)"
                500 -> "❌ SERVER ERROR (HTTP 500)" 
                else -> "⚠️ HTTP $responseCode"
            }
        } catch (e: java.net.ConnectException) {
            "❌ CONNECTION REFUSED"
        } catch (e: java.net.SocketTimeoutException) {
            "⏱️ TIMEOUT"
        } catch (e: java.net.UnknownHostException) {
            "❌ UNKNOWN HOST"
        } catch (e: Exception) {
            "❌ ERROR: ${e.message}"
        }
    }
    
    private suspend fun testOllamaVersion(baseUrl: String): String = withContext(Dispatchers.IO) {
        try {
            val connection = URL("$baseUrl/api/version").openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            
            if (connection.responseCode == 200) {
                val response = connection.inputStream.bufferedReader().readText()
                "✅ $response"
            } else {
                "❌ HTTP ${connection.responseCode}"
            }
        } catch (e: Exception) {
            "❌ ${e.javaClass.simpleName}"
        }
    }
    
    private suspend fun testOllamaTags(baseUrl: String): String = withContext(Dispatchers.IO) {
        try {
            val connection = URL("$baseUrl/api/tags").openConnection() as HttpURLConnection
            connection.connectTimeout = 3000
            connection.readTimeout = 3000
            
            if (connection.responseCode == 200) {
                val response = connection.inputStream.bufferedReader().readText()
                val modelCount = response.split("\"name\"").size - 1
                "✅ $modelCount models found"
            } else {
                "❌ HTTP ${connection.responseCode}"
            }
        } catch (e: Exception) {
            "❌ ${e.javaClass.simpleName}"
        }
    }
}
