// Cross-Platform Chat JavaScript
class ChatBot {
    constructor() {
        this.conversationId = this.generateConversationId();
        this.currentModel = 'gemma3:latest';
        this.isConnected = false;
        this.init();
    }

    init() {
        this.checkConnection();
        this.updateConnectionStatus();
        this.loadModelSelect();
    }

    generateConversationId() {
        return 'chat-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    async checkConnection() {
        try {
            const response = await fetch('/api/chat/health');
            const data = await response.json();
            this.isConnected = response.ok;
            this.updateConnectionStatus(this.isConnected, data);
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus(false, { error: error.message });
        }
    }

    updateConnectionStatus(connected = this.isConnected, data = null) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status-error';
        }
    }

    loadModelSelect() {
        // Set default model
        const modelSelect = document.getElementById('model-select');
        modelSelect.value = this.currentModel;
    }

    addMessage(content, isUser = false, timestamp = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const now = timestamp || new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${isUser ? '' : '<strong>Assistant:</strong> '}${this.formatMessage(content)}
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageDiv;
    }

    formatMessage(content) {
        // Basic HTML escaping and formatting
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Check connection
        if (!this.isConnected) {
            await this.checkConnection();
            if (!this.isConnected) {
                this.addMessage('⚠️ Cannot connect to the chatbot service. Please check if the service is running.', false);
                return;
            }
        }
        
        // Add user message
        this.addMessage(message, true);
        messageInput.value = '';
        
        // Update UI to show loading
        sendButton.disabled = true;
        sendButton.querySelector('.send-text').style.display = 'none';
        sendButton.querySelector('.send-loading').style.display = 'inline';
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId,
                    model: this.currentModel
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.response) {
                this.addMessage(data.response, false);
                
                // Update model if different
                if (data.model_used && data.model_used !== this.currentModel) {
                    this.currentModel = data.model_used;
                    document.getElementById('model-select').value = this.currentModel;
                }
            } else {
                this.addMessage('⚠️ Sorry, I received an empty response. Please try again.', false);
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage(`⚠️ Error: ${error.message}. Please try again or check your connection.`, false);
            this.isConnected = false;
            this.updateConnectionStatus();
        } finally {
            // Reset button state
            sendButton.disabled = false;
            sendButton.querySelector('.send-text').style.display = 'inline';
            sendButton.querySelector('.send-loading').style.display = 'none';
            messageInput.focus();
        }
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the current conversation?')) {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        <strong>Assistant:</strong> Hello! I'm your AI assistant powered by Ollama. I can help you with conversations and translations. How can I assist you today?
                    </div>
                    <div class="message-time"></div>
                </div>
            `;
            this.conversationId = this.generateConversationId();
        }
    }

    changeModel() {
        const modelSelect = document.getElementById('model-select');
        this.currentModel = modelSelect.value;
        this.addMessage(`🔄 Switched to model: ${this.currentModel}`, false);
    }

    async showConversations() {
        const modal = document.getElementById('conversations-modal');
        const conversationsList = document.getElementById('conversations-list');
        
        modal.style.display = 'block';
        conversationsList.innerHTML = 'Loading conversations...';
        
        try {
            const response = await fetch('/api/chat/conversations');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const conversations = await response.json();
            
            if (conversations.length === 0) {
                conversationsList.innerHTML = '<p>No conversation history found.</p>';
            } else {
                conversationsList.innerHTML = conversations.map(conv => `
                    <div class="conversation-item" style="
                        padding: 12px;
                        margin: 8px 0;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        cursor: pointer;
                        transition: background-color 0.2s ease;
                    " onclick="chatBot.loadConversation('${conv.conversation_id}')">
                        <div style="font-weight: 600; margin-bottom: 4px;">${conv.title}</div>
                        <div style="font-size: 0.85rem; color: #64748b;">
                            ${conv.message_count} messages • ${new Date(conv.last_message_at).toLocaleDateString()}
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">
                            Model: ${conv.model_used} • Platform: ${conv.platform}
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            conversationsList.innerHTML = `<p style="color: #ef4444;">Error loading conversations: ${error.message}</p>`;
        }
    }

    async loadConversation(conversationId) {
        try {
            // This would require implementing a conversation details endpoint
            console.log('Loading conversation:', conversationId);
            this.closeModal();
            this.addMessage(`📋 Loading conversation ${conversationId} (feature coming soon)`, false);
        } catch (error) {
            this.addMessage(`⚠️ Error loading conversation: ${error.message}`, false);
        }
    }

    closeModal() {
        document.getElementById('conversations-modal').style.display = 'none';
    }
}

// Global functions for HTML onclick events
function sendMessage() {
    chatBot.sendMessage();
}

function clearChat() {
    chatBot.clearChat();
}

function changeModel() {
    chatBot.changeModel();
}

function showConversations() {
    chatBot.showConversations();
}

function closeModal() {
    chatBot.closeModal();
}

// Initialize chatbot when page loads
let chatBot;
document.addEventListener('DOMContentLoaded', function() {
    chatBot = new ChatBot();
});

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('conversations-modal');
    if (event.target === modal) {
        chatBot.closeModal();
    }
}
