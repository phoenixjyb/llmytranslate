/**
 * Chat Integration Enhancement for Streaming TTS
 * 
 * This script modifies the existing ChatBot class to integrate streaming TTS functionality.
 * It intercepts the sendMessage method and enhances it with streaming capabilities.
 * 
 * Usage: Include this script after the main chat.js and streaming-tts-production.js
 */

(function() {
    'use strict';
    
    console.log('🎵 Initializing Streaming TTS integration with existing chat system...');
    
    // Wait for both ChatBot and StreamingTTSManager to be available
    function initializeStreamingIntegration() {
        if (typeof window.ChatBot === 'undefined' || typeof window.StreamingTTSManager === 'undefined') {
            console.log('⏳ Waiting for ChatBot and StreamingTTSManager...');
            setTimeout(initializeStreamingIntegration, 100);
            return;
        }
        
        // Store reference to original ChatBot
        const OriginalChatBot = window.ChatBot;
        
        // Create enhanced ChatBot class
        class EnhancedChatBot extends OriginalChatBot {
            constructor(...args) {
                super(...args);
                
                // Initialize streaming TTS manager
                this.streamingTTS = new StreamingTTSManager(this);
                
                // Store original sendMessage method
                this.originalSendMessage = this.sendMessage.bind(this);
                
                // Override sendMessage to use streaming TTS
                this.sendMessage = this.enhancedSendMessage.bind(this);
                
                console.log('🎵 Enhanced ChatBot initialized with streaming TTS');
            }
            
            async enhancedSendMessage() {
                const messageInput = document.getElementById('message-input');
                const message = messageInput.value.trim();
                
                if (!message) return;
                
                // Try streaming TTS first if enabled and connected
                if (this.streamingTTS.streamingEnabled && this.streamingTTS.isConnected) {
                    console.log('🎵 Attempting streaming TTS response...');
                    
                    const success = await this.streamingTTS.enhanceSendMessage(
                        this.originalSendMessage, 
                        message
                    );
                    
                    if (success) {
                        console.log('✅ Streaming TTS request sent successfully');
                        return; // Don't proceed with traditional send
                    }
                }
                
                // Fall back to original sendMessage
                console.log('🔄 Falling back to traditional chat');
                return this.originalSendMessage();
            }
            
            // Override addMessage to handle streaming responses
            addMessage(content, isUser = false, messageId = null) {
                // If this is a streaming message, don't add it normally
                if (!isUser && this.streamingTTS.isStreaming) {
                    console.log('🎵 Skipping regular message add - streaming active');
                    return;
                }
                
                // Call original addMessage for user messages and non-streaming responses
                return super.addMessage(content, isUser, messageId);
            }
            
            // Enhanced notification system
            showNotification(message, type = 'info', duration = 5000) {
                // Create notification if it doesn't exist
                let notification = document.querySelector('.chat-notification');
                
                if (!notification) {
                    notification = document.createElement('div');
                    notification.className = 'chat-notification';
                    document.body.appendChild(notification);
                }
                
                // Set notification content and style
                notification.textContent = message;
                notification.className = `chat-notification notification-${type} show`;
                
                // Auto-hide after duration
                setTimeout(() => {
                    notification.classList.remove('show');
                }, duration);
                
                console.log(`📢 ${type.toUpperCase()}: ${message}`);
            }
        }
        
        // Replace the global ChatBot with enhanced version
        window.ChatBot = EnhancedChatBot;
        
        // If there's already a chatBot instance, enhance it
        if (window.chatBot && window.chatBot instanceof OriginalChatBot) {
            console.log('🎵 Enhancing existing chatBot instance...');
            
            // Create new enhanced instance with existing data
            const enhancedInstance = new EnhancedChatBot();
            
            // Transfer key properties
            enhancedInstance.conversationId = window.chatBot.conversationId;
            enhancedInstance.currentModel = window.chatBot.currentModel;
            enhancedInstance.isGuest = window.chatBot.isGuest;
            enhancedInstance.guestLimits = window.chatBot.guestLimits;
            
            // Replace global instance
            window.chatBot = enhancedInstance;
        }
        
        console.log('✅ Streaming TTS integration completed successfully!');
        
        // Add integration styles
        addIntegrationStyles();
    }
    
    function addIntegrationStyles() {
        const integrationStyles = `
            .chat-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                font-size: 14px;
                z-index: 10000;
                transform: translateX(100%);
                transition: transform 0.3s ease;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .chat-notification.show {
                transform: translateX(0);
            }
            
            .notification-success {
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            }
            
            .notification-info {
                background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            }
            
            .notification-warning {
                background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            }
            
            .notification-error {
                background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            }
            
            /* Enhanced chat controls layout */
            .chat-controls {
                display: flex;
                align-items: center;
                gap: 12px;
                flex-wrap: wrap;
            }
            
            /* Ensure message input takes available space */
            #message-input {
                flex: 1;
                min-width: 200px;
            }
            
            /* Style the enhanced send button area */
            .send-button-area {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            /* Loading indicator for streaming */
            .chat-loading.streaming {
                background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
                border-color: #38b2ac;
            }
            
            .chat-loading.streaming::after {
                content: "🎵 AI is thinking and speaking...";
                color: #234e52;
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.textContent = integrationStyles;
        document.head.appendChild(styleSheet);
    }
    
    // Start the integration process
    initializeStreamingIntegration();
    
})();

console.log('🎵 Streaming TTS chat integration script loaded!');
