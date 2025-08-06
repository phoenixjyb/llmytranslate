@file:OptIn(ExperimentalMaterial3Api::class, ExperimentalComposeUiApi::class)

package com.llmytranslate.android.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.ExperimentalComposeUiApi

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EnhancedInputArea(
    currentInput: String,
    onInputChange: (String) -> Unit,
    onSendMessage: () -> Unit,
    onStartVoiceInput: () -> Unit,
    onStopVoiceInput: () -> Unit,
    isVoiceInputActive: Boolean,
    isProcessing: Boolean,
    isNativeMode: Boolean,
    modifier: Modifier = Modifier
) {
    val keyboardController = LocalSoftwareKeyboardController.current
    
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Bottom
            ) {
                OutlinedTextField(
                    value = currentInput,
                    onValueChange = onInputChange,
                    modifier = Modifier.weight(1f),
                    placeholder = { 
                        Text("Type your message...") 
                    },
                    keyboardOptions = KeyboardOptions(
                        imeAction = ImeAction.Send
                    ),
                    keyboardActions = KeyboardActions(
                        onSend = {
                            if (currentInput.isNotBlank()) {
                                onSendMessage()
                                keyboardController?.hide()
                            }
                        }
                    ),
                    enabled = !isProcessing,
                    shape = RoundedCornerShape(24.dp),
                    maxLines = 3
                )
                
                Spacer(modifier = Modifier.width(8.dp))
                
                // Voice input button
                FloatingActionButton(
                    onClick = {
                        if (isVoiceInputActive) {
                            onStopVoiceInput()
                        } else {
                            onStartVoiceInput()
                        }
                    },
                    modifier = Modifier.size(48.dp),
                    containerColor = if (isVoiceInputActive) {
                        MaterialTheme.colorScheme.error
                    } else {
                        MaterialTheme.colorScheme.primary
                    }
                ) {
                    Icon(
                        imageVector = if (isVoiceInputActive) {
                            Icons.Default.Stop
                        } else {
                            Icons.Default.Mic
                        },
                        contentDescription = if (isVoiceInputActive) {
                            "Stop voice input"
                        } else {
                            "Start voice input"
                        },
                        tint = if (isVoiceInputActive) {
                            MaterialTheme.colorScheme.onError
                        } else {
                            MaterialTheme.colorScheme.onPrimary
                        }
                    )
                }
                
                Spacer(modifier = Modifier.width(8.dp))
                
                // Send button
                FloatingActionButton(
                    onClick = {
                        if (currentInput.isNotBlank()) {
                            onSendMessage()
                            keyboardController?.hide()
                        }
                    },
                    modifier = Modifier.size(48.dp),
                    containerColor = if (currentInput.isNotBlank() && !isProcessing) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.surfaceVariant
                    }
                ) {
                    if (isProcessing) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Send,
                            contentDescription = "Send message",
                            tint = if (currentInput.isNotBlank()) {
                                MaterialTheme.colorScheme.onPrimary
                            } else {
                                MaterialTheme.colorScheme.onSurfaceVariant
                            }
                        )
                    }
                }
            }
            
            if (isNativeMode) {
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = "🎤 Native voice mode enabled",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}
