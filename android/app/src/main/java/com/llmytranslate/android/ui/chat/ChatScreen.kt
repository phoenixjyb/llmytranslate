package com.llmytranslate.android.ui.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.llmytranslate.android.models.ConnectionState
import com.llmytranslate.android.models.Message
import com.llmytranslate.android.viewmodels.ChatViewModel
import java.text.SimpleDateFormat
import java.util.*

/**
 * Chat screen for text-based conversation with LLMyTranslate server.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    onNavigateToVoice: () -> Unit,
    onNavigateToSettings: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    
    var inputText by remember { mutableStateOf("") }
    
    LaunchedEffect(Unit) {
        viewModel.initialize()
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Top bar with connection status and navigation
        TopAppBar(
            title = { 
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("LLMyTranslate")
                    Spacer(modifier = Modifier.width(8.dp))
                    ConnectionStatusIndicator(connectionState)
                }
            },
            actions = {
                IconButton(onClick = onNavigateToVoice) {
                    Icon(Icons.Default.Mic, contentDescription = "Voice Chat")
                }
                IconButton(onClick = onNavigateToSettings) {
                    Icon(Icons.Default.Settings, contentDescription = "Settings")
                }
            }
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Connection status card
        if (connectionState != ConnectionState.CONNECTED) {
            ConnectionStatusCard(
                connectionState = connectionState,
                onRetry = { viewModel.retryConnection() }
            )
            Spacer(modifier = Modifier.height(8.dp))
        }
        
        // Chat messages
        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            reverseLayout = true // Show newest messages at bottom
        ) {
            items(uiState.messages.reversed()) { message ->
                ChatMessageItem(message = message)
            }
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Input area
        ChatInputArea(
            inputText = inputText,
            onTextChange = { inputText = it },
            onSendMessage = {
                if (inputText.isNotBlank()) {
                    viewModel.sendMessage(inputText)
                    inputText = ""
                }
            },
            isLoading = uiState.isLoading,
            isConnected = connectionState == ConnectionState.CONNECTED
        )
        
        // Error display
        uiState.errorMessage?.let { error ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer
                )
            ) {
                Text(
                    text = error,
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }
    }
}

@Composable
fun ConnectionStatusIndicator(connectionState: ConnectionState) {
    val (color, icon) = when (connectionState) {
        ConnectionState.CONNECTED -> Color.Green to Icons.Default.Wifi
        ConnectionState.CONNECTING -> Color.Orange to Icons.Default.WifiFind
        ConnectionState.RECONNECTING -> Color.Orange to Icons.Default.Refresh
        ConnectionState.ERROR -> Color.Red to Icons.Default.WifiOff
        ConnectionState.DISCONNECTED -> Color.Gray to Icons.Default.WifiOff
    }
    
    Icon(
        imageVector = icon,
        contentDescription = connectionState.name,
        tint = color,
        modifier = Modifier.size(16.dp)
    )
}

@Composable
fun ConnectionStatusCard(
    connectionState: ConnectionState,
    onRetry: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = when (connectionState) {
                ConnectionState.ERROR -> MaterialTheme.colorScheme.errorContainer
                ConnectionState.CONNECTING, ConnectionState.RECONNECTING -> MaterialTheme.colorScheme.tertiaryContainer
                else -> MaterialTheme.colorScheme.surfaceVariant
            }
        )
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = when (connectionState) {
                    ConnectionState.ERROR -> Icons.Default.Error
                    ConnectionState.CONNECTING, ConnectionState.RECONNECTING -> Icons.Default.Refresh
                    else -> Icons.Default.Info
                },
                contentDescription = null,
                modifier = Modifier.size(24.dp)
            )
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = when (connectionState) {
                        ConnectionState.CONNECTING -> "Connecting to server..."
                        ConnectionState.RECONNECTING -> "Reconnecting..."
                        ConnectionState.ERROR -> "Connection failed"
                        ConnectionState.DISCONNECTED -> "Not connected"
                        else -> "Status unknown"
                    },
                    style = MaterialTheme.typography.titleSmall
                )
                
                Text(
                    text = when (connectionState) {
                        ConnectionState.CONNECTING -> "Looking for LLMyTranslate server"
                        ConnectionState.RECONNECTING -> "Attempting to reconnect"
                        ConnectionState.ERROR -> "Check your network connection"
                        ConnectionState.DISCONNECTED -> "Tap retry to connect"
                        else -> ""
                    },
                    style = MaterialTheme.typography.bodySmall
                )
            }
            
            if (connectionState == ConnectionState.ERROR || connectionState == ConnectionState.DISCONNECTED) {
                Button(onClick = onRetry) {
                    Text("Retry")
                }
            }
        }
    }
}

@Composable
fun ChatMessageItem(message: Message) {
    val timeFormat = SimpleDateFormat("HH:mm", Locale.getDefault())
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isFromUser) Arrangement.End else Arrangement.Start
    ) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(12.dp))
                .background(
                    if (message.isFromUser) 
                        MaterialTheme.colorScheme.primary 
                    else 
                        MaterialTheme.colorScheme.surfaceVariant
                )
                .padding(12.dp)
                .widthIn(max = 280.dp)
        ) {
            Column {
                Text(
                    text = message.content,
                    color = if (message.isFromUser) 
                        MaterialTheme.colorScheme.onPrimary 
                    else 
                        MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium
                )
                
                Spacer(modifier = Modifier.height(4.dp))
                
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = timeFormat.format(message.timestamp),
                        color = if (message.isFromUser) 
                            MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                        else 
                            MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                        style = MaterialTheme.typography.labelSmall
                    )
                    
                    message.processingTime?.let { time ->
                        Text(
                            text = " • ${time.toInt()}ms",
                            color = if (message.isFromUser) 
                                MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                            else 
                                MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatInputArea(
    inputText: String,
    onTextChange: (String) -> Unit,
    onSendMessage: () -> Unit,
    isLoading: Boolean,
    isConnected: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Bottom
    ) {
        OutlinedTextField(
            value = inputText,
            onValueChange = onTextChange,
            modifier = Modifier.weight(1f),
            placeholder = { 
                Text(
                    if (isConnected) "Type your message..." 
                    else "Connect to server to chat"
                ) 
            },
            enabled = isConnected && !isLoading,
            maxLines = 4
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        FloatingActionButton(
            onClick = onSendMessage,
            modifier = Modifier.size(56.dp),
            containerColor = MaterialTheme.colorScheme.primary
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Icon(
                    imageVector = Icons.Default.Send,
                    contentDescription = "Send message",
                    tint = MaterialTheme.colorScheme.onPrimary
                )
            }
        }
    }
}
