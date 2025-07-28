// Cross-Platform Chat JavaScript with User Authentication
class ChatBot {
    constructor() {
        this.conversationId = this.generateConversationId();
        this.currentModel = 'gemma3:latest';
        this.isConnected = false;
        this.userAuth = null;
        this.currentUser = null;
        this.isGuest = false;
        this.sessionId = null;
        this.guestLimits = {
            maxConversations: 5,
            maxMessagesPerConversation: 20,
            currentConversationMessages: 0
        };
        this.init();
    }

    init() {
        this.checkUserAuthentication();
        this.checkConnection();
        this.updateConnectionStatus();
        this.loadModelSelect();
        this.setupUserInterface();
    }

    generateConversationId() {
        return 'chat-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    async checkUserAuthentication() {
        try {
            const response = await fetch('/api/users/status', {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const status = await response.json();
                this.isGuest = status.is_guest;
                this.currentUser = status.authenticated ? {
                    username: status.username,
                    role: status.role,
                    sessionId: status.session_id
                } : null;
                this.sessionId = status.session_id;
                
                // Update UI based on authentication status
                this.updateUserInterface();
                
                // Get guest limits if user is a guest
                if (this.isGuest) {
                    await this.loadGuestInfo();
                }
            } else {
                // No authentication, redirect to auth page
                this.redirectToAuth();
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            this.redirectToAuth();
        }
    }

    async loadGuestInfo() {
        try {
            const response = await fetch('/api/users/guest-info', {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                const guestInfo = await response.json();
                if (guestInfo.is_guest && guestInfo.guest_limits) {
                    this.guestLimits = {
                        maxConversations: guestInfo.guest_limits.max_conversations,
                        maxMessagesPerConversation: guestInfo.guest_limits.max_messages_per_conversation,
                        currentConversationMessages: 0
                    };
                }
            }
        } catch (error) {
            console.error('Failed to load guest info:', error);
        }
    }

    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        const token = localStorage.getItem('auth_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const guestSessionId = localStorage.getItem('guest_session_id');
        if (guestSessionId && !token) {
            headers['X-Guest-Session-Id'] = guestSessionId;
        }

        return headers;
    }

    updateUserInterface() {
        // Update user info in the interface
        const userInfoElement = document.getElementById('user-info');
        if (userInfoElement) {
            if (this.isGuest) {
                userInfoElement.innerHTML = `
                    <span class="guest-badge">Guest User</span>
                    <button onclick="chatBot.showUpgradePrompt()" class="upgrade-btn">Sign Up</button>
                `;
            } else if (this.currentUser) {
                userInfoElement.innerHTML = `
                    <span class="user-name">Welcome, ${this.currentUser.username}</span>
                    <div class="user-menu">
                        <button onclick="chatBot.showUserMenu()" class="user-menu-btn">⚙️</button>
                    </div>
                `;
            }
        }

        // Show guest limitations if applicable
        if (this.isGuest) {
            this.showGuestLimitations();
        }
    }

    showGuestLimitations() {
        const messagesContainer = document.getElementById('chat-messages');
        const limitationNotice = document.createElement('div');
        limitationNotice.className = 'guest-limitation-notice';
        limitationNotice.innerHTML = `
            <div class="limitation-content">
                <h4>🚀 You're using Guest Mode</h4>
                <p>Limited to ${this.guestLimits.maxMessagesPerConversation} messages per conversation</p>
                <button onclick="chatBot.showUpgradePrompt()" class="upgrade-btn-small">Sign Up for Unlimited Access</button>
            </div>
        `;
        
        // Insert at the top of messages
        if (messagesContainer.firstChild) {
            messagesContainer.insertBefore(limitationNotice, messagesContainer.firstChild);
        } else {
            messagesContainer.appendChild(limitationNotice);
        }
    }

    showUpgradePrompt() {
        const modal = document.createElement('div');
        modal.className = 'upgrade-modal';
        modal.innerHTML = `
            <div class="modal-content upgrade-content">
                <div class="modal-header">
                    <h2>🚀 Upgrade Your Experience</h2>
                    <span class="close" onclick="chatBot.dismissUpgradeModal(this)">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="upgrade-benefits">
                        <h3>Get Unlimited Access</h3>
                        <ul>
                            <li>✓ Unlimited conversations</li>
                            <li>✓ Persistent chat history</li>
                            <li>✓ Profile customization</li>
                            <li>✓ Priority model access</li>
                            <li>✓ Advanced features</li>
                        </ul>
                        <div class="upgrade-actions">
                            <button onclick="chatBot.redirectToAuth()" class="btn-primary">Sign Up Now</button>
                            <button onclick="chatBot.dismissUpgradeModal(this)" class="btn-secondary">Continue as Guest</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    setupUserInterface() {
        // Add user interface elements to the chat
        const chatContainer = document.querySelector('.chat-container') || document.body;
        
        // Add user info section if it doesn't exist
        if (!document.getElementById('user-info')) {
            const userInfoDiv = document.createElement('div');
            userInfoDiv.id = 'user-info';
            userInfoDiv.className = 'user-info-section';
            
            // Insert at the beginning of chat container
            if (chatContainer.firstChild) {
                chatContainer.insertBefore(userInfoDiv, chatContainer.firstChild);
            } else {
                chatContainer.appendChild(userInfoDiv);
            }
        }
    }

    redirectToAuth() {
        window.location.href = '/auth.html';
    }

    dismissUpgradeModal(buttonElement) {
        // Find the modal element safely
        let modalElement = buttonElement;
        let attempts = 0;
        
        // Traverse up the DOM to find the modal
        while (modalElement && attempts < 10) {
            if (modalElement.classList && modalElement.classList.contains('upgrade-modal')) {
                modalElement.remove();
                return;
            }
            modalElement = modalElement.parentElement;
            attempts++;
        }
        
        // Fallback: remove any upgrade modal found in the document
        const upgradeModals = document.querySelectorAll('.upgrade-modal');
        upgradeModals.forEach(modal => modal.remove());
    }

    async checkConnection() {
        try {
            const response = await fetch('/api/chat/health', {
                headers: this.getAuthHeaders()
            });
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

    addMessage(content, isUser = false, timestamp = null, skipApi = false) {
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
        
        // Check guest limitations
        if (this.isGuest) {
            if (this.guestLimits.currentConversationMessages >= this.guestLimits.maxMessagesPerConversation) {
                this.addMessage('🚫 Guest limit reached. Sign up for unlimited conversations!', false);
                this.showUpgradePrompt();
                return;
            }
        }
        
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
        
        // Update guest message count
        if (this.isGuest) {
            this.guestLimits.currentConversationMessages++;
        }
        
        // Update UI to show loading
        sendButton.disabled = true;
        sendButton.querySelector('.send-text').style.display = 'none';
        sendButton.querySelector('.send-loading').style.display = 'inline';
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: this.getAuthHeaders(),
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
                
                // Update guest message count for bot response
                if (this.isGuest) {
                    this.guestLimits.currentConversationMessages++;
                    this.updateGuestLimitDisplay();
                }
                
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

    updateGuestLimitDisplay() {
        if (!this.isGuest) return;
        
        const remaining = this.guestLimits.maxMessagesPerConversation - this.guestLimits.currentConversationMessages;
        const limitationNotice = document.querySelector('.guest-limitation-notice');
        
        if (limitationNotice) {
            const content = limitationNotice.querySelector('.limitation-content p');
            if (content) {
                content.textContent = `${remaining} messages remaining in this conversation`;
                
                if (remaining <= 3) {
                    limitationNotice.classList.add('warning');
                }
                if (remaining <= 0) {
                    limitationNotice.classList.add('limit-reached');
                }
            }
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
            
            // Reset guest message count
            if (this.isGuest) {
                this.guestLimits.currentConversationMessages = 0;
                this.showGuestLimitations();
            }
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
            const response = await fetch('/api/chat/conversations', {
                headers: this.getAuthHeaders()
            });
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
            
            // Add guest notice at the bottom
            if (this.isGuest) {
                conversationsList.innerHTML += `
                    <div style="
                        margin-top: 16px;
                        padding: 12px;
                        background-color: #fef3cd;
                        border: 1px solid #fbbf24;
                        border-radius: 8px;
                        font-size: 0.9rem;
                        color: #92400e;
                    ">
                        💡 <strong>Guest Mode:</strong> Your conversations are temporary and will be lost when you close the browser. 
                        <a href="#" onclick="chatBot.redirectToAuth()" style="color: #1d4ed8; text-decoration: underline;">Sign up</a> to save your chats permanently!
                    </div>
                `;
            }
        } catch (error) {
            conversationsList.innerHTML = `<p style="color: #ef4444;">Error loading conversations: ${error.message}</p>`;
        }
    }

    async loadConversation(conversationId) {
        try {
            this.closeModal();
            
            // Clear current chat
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';
            
            // Show loading message
            this.addMessage('📋 Loading conversation history...', false, null, true);
            
            // Fetch conversation history
            const response = await fetch(`/api/chat/conversations/${conversationId}/history`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`Failed to load conversation: ${response.status}`);
            }

            const history = await response.json();
            
            // Clear loading message
            chatMessages.innerHTML = '';
            
            // Set current conversation ID
            this.conversationId = conversationId;
            
            // Load all messages from history
            if (history.messages && history.messages.length > 0) {
                history.messages.forEach(message => {
                    const isUser = message.role === 'user';
                    const messageTime = message.timestamp ? new Date(message.timestamp) : null;
                    this.addMessage(message.content, isUser, messageTime, true); // true = skip API
                });
                
                // Update message count for guests
                if (this.isGuest) {
                    this.guestLimits.currentConversationMessages = history.messages.length;
                }
                
                // Add a separator to indicate loaded history
                this.addMessage('--- Conversation restored ---', false, null, true);
            } else {
                this.addMessage('📋 Empty conversation loaded. You can continue chatting!', false, null, true);
            }
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
        } catch (error) {
            console.error('Load conversation error:', error);
            this.addMessage(`⚠️ Error loading conversation: ${error.message}`, false, null, true);
        }
    }

    closeModal() {
        const modal = document.getElementById('conversations-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    showUserMenu() {
        const modal = document.createElement('div');
        modal.className = 'user-menu-modal';
        modal.innerHTML = `
            <div class="modal-content user-menu-content">
                <div class="modal-header">
                    <h2>User Menu</h2>
                    <span class="close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="user-menu-options">
                        <button onclick="chatBot.showProfile()" class="menu-option">👤 Profile</button>
                        <button onclick="chatBot.showSettings()" class="menu-option">⚙️ Settings</button>
                        <button onclick="chatBot.showUsageStats()" class="menu-option">📊 Usage Stats</button>
                        <button onclick="chatBot.logout()" class="menu-option logout">🚪 Logout</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async logout() {
        try {
            await fetch('/api/users/logout', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
        } catch (error) {
            console.error('Logout error:', error);
        }

        // Clear local storage
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('guest_session_id');

        // Redirect to auth page
        this.redirectToAuth();
    }

    showProfile() {
        // Implement profile viewing/editing
        this.addMessage('📋 Profile management feature coming soon!', false);
    }

    showSettings() {
        // Implement settings
        this.addMessage('⚙️ Settings feature coming soon!', false);
    }

    showUsageStats() {
        // Implement usage statistics
        this.addMessage('📊 Usage statistics feature coming soon!', false);
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
