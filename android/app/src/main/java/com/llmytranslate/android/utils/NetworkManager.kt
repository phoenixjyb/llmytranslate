package com.llmytranslate.android.utils

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.util.Log
import com.llmytranslate.android.models.ServerInfo
import com.squareup.moshi.Moshi
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.net.InetAddress
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * NetworkManager handles server discovery and network utilities.
 * Automatically discovers LLMyTranslate servers on the local network.
 */
@Singleton
class NetworkManager @Inject constructor(
    private val context: Context,
    private val httpClient: OkHttpClient,
    private val moshi: Moshi
) {
    
    companion object {
        private const val TAG = "NetworkManager"
        private val COMMON_PORTS = listOf(8000, 8080, 3000, 5000, 8888)
        private const val DISCOVERY_TIMEOUT_MS = 2000L
        private const val MAX_CONCURRENT_SCANS = 20
    }
    
    private val serverInfoAdapter = moshi.adapter(ServerInfo::class.java)
    
    /**
     * Discover LLMyTranslate servers on the local network.
     * Scans common ports and validates server responses.
     */
    suspend fun discoverServers(): List<ServerDiscoveryResult> = withContext(Dispatchers.IO) {
        val results = mutableListOf<ServerDiscoveryResult>()
        
        try {
            val localIpRange = getLocalIpRange()
            if (localIpRange.isEmpty()) {
                Log.w(TAG, "Could not determine local IP range")
                return@withContext results
            }
            
            Log.i(TAG, "Scanning IP range: $localIpRange")
            
            // Scan each IP in the range
            localIpRange.chunked(MAX_CONCURRENT_SCANS).forEach { ipChunk ->
                val scanResults = ipChunk.map { ip ->
                    kotlinx.coroutines.async {
                        scanHostForLLMyTranslate(ip)
                    }
                }.map { it.await() }
                
                results.addAll(scanResults.filterNotNull())
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error during server discovery", e)
        }
        
        Log.i(TAG, "Server discovery completed. Found ${results.size} servers.")
        results
    }
    
    /**
     * Test connection to a specific server.
     */
    suspend fun testServerConnection(host: String, port: Int): ServerDiscoveryResult? = 
        withContext(Dispatchers.IO) {
            scanHostForLLMyTranslate("$host:$port")
        }
    
    /**
     * Get the local IP address range for network scanning.
     */
    private fun getLocalIpRange(): List<String> {
        try {
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val dhcp = wifiManager.dhcpInfo
            
            if (dhcp.ipAddress == 0) {
                Log.w(TAG, "No IP address available")
                return emptyList()
            }
            
            // Convert IP address to string
            val ipAddress = String.format(
                "%d.%d.%d.%d",
                dhcp.ipAddress and 0xff,
                dhcp.ipAddress shr 8 and 0xff,
                dhcp.ipAddress shr 16 and 0xff,
                dhcp.ipAddress shr 24 and 0xff
            )
            
            // Generate IP range (e.g., 192.168.1.1 to 192.168.1.255)
            val baseIP = ipAddress.substringBeforeLast(".")
            return (1..254).map { "$baseIP.$it" }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error getting local IP range", e)
            return emptyList()
        }
    }
    
    /**
     * Scan a specific host for LLMyTranslate service.
     */
    private suspend fun scanHostForLLMyTranslate(host: String): ServerDiscoveryResult? {
        for (port in COMMON_PORTS) {
            try {
                val baseUrl = "http://$host:$port"
                val discoveryUrl = "$baseUrl/api/android/discover"
                
                Log.d(TAG, "Checking $discoveryUrl")
                
                val request = Request.Builder()
                    .url(discoveryUrl)
                    .header("User-Agent", "LLMyTranslate-Android")
                    .build()
                
                val client = httpClient.newBuilder()
                    .connectTimeout(DISCOVERY_TIMEOUT_MS, TimeUnit.MILLISECONDS)
                    .readTimeout(DISCOVERY_TIMEOUT_MS, TimeUnit.MILLISECONDS)
                    .build()
                
                val response = client.newCall(request).execute()
                
                if (response.isSuccessful) {
                    val responseBody = response.body?.string()
                    if (responseBody != null) {
                        val serverInfo = serverInfoAdapter.fromJson(responseBody)
                        if (serverInfo != null) {
                            Log.i(TAG, "Found LLMyTranslate server: $baseUrl")
                            return ServerDiscoveryResult(
                                host = host,
                                port = port,
                                baseUrl = baseUrl,
                                serverInfo = serverInfo,
                                responseTime = System.currentTimeMillis() // Simple timing
                            )
                        }
                    }
                }
                
            } catch (e: Exception) {
                Log.d(TAG, "No LLMyTranslate service on $host:$port - ${e.message}")
            }
        }
        
        return null
    }
    
    /**
     * Check if the device is connected to WiFi.
     */
    fun isWiFiConnected(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }
    
    /**
     * Check if the device has internet connectivity.
     */
    fun hasInternetConnection(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
               capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
    
    /**
     * Get the current WiFi network name (SSID).
     */
    fun getCurrentWiFiName(): String? {
        try {
            val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
            val wifiInfo = wifiManager.connectionInfo
            return wifiInfo.ssid?.removeSurrounding("\"")
        } catch (e: Exception) {
            Log.e(TAG, "Error getting WiFi name", e)
            return null
        }
    }
    
    /**
     * Test network latency to a server.
     */
    suspend fun testLatency(host: String, port: Int): Long = withContext(Dispatchers.IO) {
        try {
            val startTime = System.currentTimeMillis()
            
            val request = Request.Builder()
                .url("http://$host:$port/api/android/health")
                .head() // HEAD request for minimal data transfer
                .build()
            
            val client = httpClient.newBuilder()
                .connectTimeout(5000, TimeUnit.MILLISECONDS)
                .readTimeout(5000, TimeUnit.MILLISECONDS)
                .build()
            
            val response = client.newCall(request).execute()
            val endTime = System.currentTimeMillis()
            
            if (response.isSuccessful) {
                endTime - startTime
            } else {
                -1L
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error testing latency to $host:$port", e)
            -1L
        }
    }
}

/**
 * Result of server discovery scan.
 */
data class ServerDiscoveryResult(
    val host: String,
    val port: Int,
    val baseUrl: String,
    val serverInfo: ServerInfo,
    val responseTime: Long
) {
    val websocketUrl: String
        get() = baseUrl.replace("http://", "ws://") + serverInfo.websocketEndpoint
}

/**
 * Network status information.
 */
data class NetworkStatus(
    val isConnected: Boolean,
    val isWiFi: Boolean,
    val hasInternet: Boolean,
    val wifiName: String?,
    val signalStrength: Int? = null
)
