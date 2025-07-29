// Cross-Platform Chat JavaScript with User Authentication
class ProgressTracker {
    constructor(container, title = 'Processing...') {
        this.container = container;
        this.title = title;
        this.startTime = Date.now();
        this.stages = [];
        this.currentStageIndex = -1;
        this.timers = {};
        this.isCompleted = false;
        this.element = null;
        
        this.init();
    }
    
    init() {
        this.element = document.createElement('div');
        this.element.className = 'progress-container';
        this.container.appendChild(this.element);
        this.render();
        this.startGlobalTimer();
    }
    
    addStage(id, text, duration = null) {
        this.stages.push({
            id,
            text,
            status: 'pending', // pending, active, completed, error
            startTime: null,
            endTime: null,
            estimatedDuration: duration
        });
        this.render();
        return this;
    }
    
    startStage(stageId, customText = null) {
        // Complete current stage if exists
        if (this.currentStageIndex >= 0) {
            this.completeStage(this.stages[this.currentStageIndex].id);
        }
        
        // Find and start new stage
        const stageIndex = this.stages.findIndex(s => s.id === stageId);
        if (stageIndex !== -1) {
            this.currentStageIndex = stageIndex;
            const stage = this.stages[stageIndex];
            stage.status = 'active';
            stage.startTime = Date.now();
            if (customText) stage.text = customText;
            
            this.render();
            console.log(`🎯 Stage started: ${stage.text}`);
        }
        return this;
    }
    
    completeStage(stageId, customText = null) {
        const stage = this.stages.find(s => s.id === stageId);
        if (stage && stage.status === 'active') {
            stage.status = 'completed';
            stage.endTime = Date.now();
            if (customText) stage.text = customText;
            
            this.render();
            console.log(`✅ Stage completed: ${stage.text} (${stage.endTime - stage.startTime}ms)`);
        }
        return this;
    }
    
    errorStage(stageId, errorText = null) {
        const stage = this.stages.find(s => s.id === stageId);
        if (stage) {
            stage.status = 'error';
            stage.endTime = Date.now();
            if (errorText) stage.text = errorText;
            
            this.render();
            console.log(`❌ Stage error: ${stage.text}`);
        }
        return this;
    }
    
    complete(successMessage = 'Completed successfully!') {
        // Complete any active stage
        if (this.currentStageIndex >= 0) {
            const activeStage = this.stages[this.currentStageIndex];
            if (activeStage.status === 'active') {
                this.completeStage(activeStage.id);
            }
        }
        
        this.isCompleted = true;
        this.title = successMessage;
        this.render();
        
        // Auto-remove after delay
        setTimeout(() => {
            if (this.element && this.element.parentNode) {
                this.element.style.animation = 'progressSlide 0.3s ease-out reverse';
                setTimeout(() => {
                    if (this.element && this.element.parentNode) {
                        this.element.remove();
                    }
                }, 300);
            }
        }, 2000);
        
        return this;
    }
    
    remove() {
        if (this.element && this.element.parentNode) {
            this.element.remove();
        }
        return this;
    }
    
    startGlobalTimer() {
        const updateTimer = () => {
            if (!this.isCompleted && this.element) {
                this.render();
                requestAnimationFrame(updateTimer);
            }
        };
        requestAnimationFrame(updateTimer);
    }
    
    formatDuration(ms) {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
    }
    
    getStageIcon(status) {
        switch (status) {
            case 'pending': return '○';
            case 'active': return '●';
            case 'completed': return '✓';
            case 'error': return '✕';
            default: return '○';
        }
    }
    
    calculateProgress() {
        const completedStages = this.stages.filter(s => s.status === 'completed').length;
        const totalStages = this.stages.length;
        return totalStages > 0 ? (completedStages / totalStages) * 100 : 0;
    }
    
    render() {
        if (!this.element) return;
        
        const elapsed = Date.now() - this.startTime;
        const progress = this.calculateProgress();
        
        const stagesHtml = this.stages.map(stage => {
            let duration = '';
            if (stage.startTime) {
                const stageDuration = stage.endTime ? 
                    stage.endTime - stage.startTime : 
                    Date.now() - stage.startTime;
                duration = this.formatDuration(stageDuration);
            }
            
            return `
                <div class="progress-stage">
                    <div class="stage-icon ${stage.status}">
                        ${this.getStageIcon(stage.status)}
                    </div>
                    <div class="stage-text ${stage.status}">
                        ${stage.text}
                    </div>
                    ${duration ? `<div class="stage-duration">${duration}</div>` : ''}
                </div>
            `;
        }).join('');
        
        this.element.innerHTML = `
            <div class="progress-header">
                <div class="progress-title">${this.title}</div>
                <div class="progress-timer">${this.formatDuration(elapsed)}</div>
            </div>
            ${stagesHtml}
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
        `;
    }
}

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
        
        // File upload properties
        this.attachedFiles = [];
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        this.supportedFileTypes = {
            images: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'],
            documents: ['pdf', 'txt', 'md', 'doc', 'docx'],
            maxFiles: 5
        };
        
        this.init();
    }

    init() {
        this.checkUserAuthentication();
        this.checkConnection();
        this.updateConnectionStatus();
        this.loadModelSelect();
        this.setupUserInterface();
        this.initFileUpload();
        this.setupKeyboardShortcuts();
    }

    setupKeyboardShortcuts() {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                // Ctrl+Enter or Cmd+Enter to send
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
                // Enter alone to send (optional - you can remove this if you prefer only Ctrl+Enter)
                else if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
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
                // No authentication, try to create guest session
                await this.createGuestSession();
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            // Try to create guest session instead of redirecting
            await this.createGuestSession();
        }
    }

    async createGuestSession() {
        try {
            console.log('Creating guest session...');
            const response = await fetch('/api/users/guest-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const guestSession = await response.json();
                console.log('Guest session created:', guestSession);
                // Store guest session ID
                localStorage.setItem('guest_session_id', guestSession.session_id);
                this.sessionId = guestSession.session_id;
                this.isGuest = true;
                this.currentUser = null;
                
                // Update UI and load guest info
                this.updateUserInterface();
                await this.loadGuestInfo();
                
                console.log('Guest session created successfully:', guestSession.session_id);
            } else {
                console.error('Failed to create guest session:', response.status, response.statusText);
                this.showConnectionError('Unable to create session. Please try again.');
            }
        } catch (error) {
            console.error('Guest session creation failed:', error);
            this.showConnectionError('Connection failed. Please check your network and try again.');
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
        const guestSessionId = localStorage.getItem('guest_session_id');
        
        console.log('Auth headers debug:', {
            token: token ? 'present' : 'missing',
            guestSessionId: guestSessionId ? guestSessionId : 'missing'
        });

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (guestSessionId && !token) {
            headers['X-Guest-Session-Id'] = guestSessionId;
        }

        console.log('Final headers:', headers);
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
        window.location.href = '/auth';
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

    showConnectionError(message) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = 'status-error';
            statusElement.textContent = message;
        }
        
        // Also show an error message in the chat
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            const errorMessage = document.createElement('div');
            errorMessage.className = 'message bot-message error-message';
            errorMessage.innerHTML = `
                <div class="message-content">
                    <strong>Error:</strong> ${message}
                </div>
            `;
            messagesContainer.appendChild(errorMessage);
        }
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

    // File upload methods
    initFileUpload() {
        console.log('Initializing file upload...');
        const fileInput = document.getElementById('file-input');
        const fileUploadBtn = document.getElementById('file-upload-btn');
        const attachedFilesContainer = document.getElementById('attached-files');
        
        console.log('File input found:', !!fileInput);
        console.log('File upload button found:', !!fileUploadBtn);
        console.log('Attached files container found:', !!attachedFilesContainer);
        
        if (fileUploadBtn) {
            fileUploadBtn.addEventListener('click', () => {
                console.log('File upload button clicked');
                fileInput.click();
            });
        } else {
            console.error('File upload button not found');
        }
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                console.log('File input changed, files:', e.target.files.length);
                this.handleFileSelection(e.target.files);
            });
        } else {
            console.error('File input not found');
        }
        
        // Drag and drop support
        const chatInput = document.getElementById('message-input');
        if (chatInput) {
            chatInput.addEventListener('dragover', (e) => {
                e.preventDefault();
                chatInput.classList.add('drag-over');
            });
            
            chatInput.addEventListener('dragleave', (e) => {
                e.preventDefault();
                chatInput.classList.remove('drag-over');
            });
            
            chatInput.addEventListener('drop', (e) => {
                e.preventDefault();
                chatInput.classList.remove('drag-over');
                this.handleFileSelection(e.dataTransfer.files);
            });
        }
    }
    
    async handleFileSelection(files) {
        console.log('handleFileSelection called with', files.length, 'files');
        this.showNotification(`Processing ${files.length} file(s)...`, 'info');
        
        for (let file of files) {
            console.log('Processing file:', file.name, 'size:', file.size, 'type:', file.type);
            
            if (this.attachedFiles.length >= this.supportedFileTypes.maxFiles) {
                this.showNotification(`Maximum ${this.supportedFileTypes.maxFiles} files allowed`, 'warning');
                break;
            }
            
            if (file.size > this.maxFileSize) {
                this.showNotification(`File "${file.name}" is too large (max 50MB)`, 'error');
                continue;
            }
            
            if (!this.isFileTypeSupported(file)) {
                console.log('File type not supported:', file.name);
                this.showNotification(`File type not supported: ${file.name}`, 'error');
                continue;
            }
            
            console.log('Converting file to base64...');
            this.showNotification(`Converting ${file.name} to base64...`, 'info');
            
            try {
                // Convert file to base64
                const fileData = await this.fileToBase64(file);
                console.log('Base64 conversion completed, length:', fileData.length);
                
                // Decode to check actual content size
                const decodedData = atob(fileData);
                const actualSize = decodedData.length;
                console.log('Original file size:', file.size, 'Decoded content size:', actualSize);
                
                const fileUpload = {
                    file_id: this.generateFileId(),
                    filename: file.name,
                    content_type: file.type,
                    file_size: actualSize, // Use actual decoded size instead of file.size
                    file_data: fileData,
                    file_category: this.getFileCategory(file.type)
                };
                
                console.log('File processed successfully:', fileUpload.filename);
                this.attachedFiles.push(fileUpload);
                this.updateAttachedFilesDisplay();
                this.showNotification(`✓ ${file.name} attached successfully`, 'success');
                
            } catch (error) {
                console.error('Error processing file:', file.name, error);
                this.showNotification(`Error processing ${file.name}: ${error.message}`, 'error');
            }
        }
        
        console.log('Total attached files:', this.attachedFiles.length);
    }
    
    isFileTypeSupported(file) {
        const extension = file.name.split('.').pop().toLowerCase();
        const allSupportedTypes = [
            ...this.supportedFileTypes.images,
            ...this.supportedFileTypes.documents
        ];
        return allSupportedTypes.includes(extension);
    }
    
    getFileCategory(contentType) {
        if (contentType.startsWith('image/')) return 'image';
        if (contentType.startsWith('text/') || contentType.includes('pdf') || contentType.includes('document')) return 'document';
        return 'other';
    }
    
    async fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // Remove the data URL prefix (e.g., "data:image/png;base64,")
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    generateFileId() {
        return 'file-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }
    
    updateAttachedFilesDisplay() {
        const container = document.getElementById('attached-files');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.attachedFiles.forEach((file, index) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'attached-file';
            fileElement.innerHTML = `
                <div class="file-info">
                    <span class="file-icon">${this.getFileIcon(file.file_category)}</span>
                    <span class="file-name">${file.filename}</span>
                    <span class="file-size">${this.formatFileSize(file.file_size)}</span>
                </div>
                <button class="remove-file-btn" onclick="chatBot.removeFile(${index})">×</button>
            `;
            container.appendChild(fileElement);
        });
        
        // Show/hide the container
        container.style.display = this.attachedFiles.length > 0 ? 'block' : 'none';
    }
    
    removeFile(index) {
        this.attachedFiles.splice(index, 1);
        this.updateAttachedFilesDisplay();
    }
    
    getFileIcon(category) {
        const icons = {
            image: '🖼️',
            document: '📄',
            other: '📎'
        };
        return icons[category] || icons.other;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showNotification(message, type = 'info') {
        // You can implement a more sophisticated notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        
        const colors = {
            info: '#3b82f6',
            warning: '#f59e0b',
            error: '#ef4444',
            success: '#10b981'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async sendMessage() {
        console.log('=== SEND MESSAGE START ===');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const message = messageInput.value.trim();
        
        console.log('Message input:', message);
        console.log('Attached files count:', this.attachedFiles.length);
        console.log('Attached files:', this.attachedFiles);
        
        if (!message && this.attachedFiles.length === 0) {
            console.log('No message and no files - exiting');
            this.showNotification('Please enter a message or attach files', 'warning');
            return;
        }
        
        // Check guest limitations
        if (this.isGuest) {
            console.log('Guest mode - checking limitations');
            if (this.guestLimits.currentConversationMessages >= this.guestLimits.maxMessagesPerConversation) {
                this.addMessage('🚫 Guest limit reached. Sign up for unlimited conversations!', false);
                this.showUpgradePrompt();
                return;
            }
        }
        
        // Check connection
        console.log('Checking connection...');
        if (!this.isConnected) {
            await this.checkConnection();
            if (!this.isConnected) {
                this.addMessage('⚠️ Cannot connect to the chatbot service. Please check if the service is running.', false);
                return;
            }
        }
        console.log('Connection check passed');
        
        // Add user message
        this.addMessage(message || '[File upload]', true);
        messageInput.value = '';
        
        // Update guest message count
        if (this.isGuest) {
            this.guestLimits.currentConversationMessages++;
        }

        // Create progress tracker
        const messagesContainer = document.getElementById('chat-messages');
        const progressTitle = this.attachedFiles.length > 0 ? 
            `Processing ${this.attachedFiles.length} file(s) and generating response...` : 
            'Generating AI response...';
        
        const progressTracker = new ProgressTracker(messagesContainer, progressTitle);
        
        // Setup progress stages based on request type
        if (this.attachedFiles.length > 0) {
            progressTracker
                .addStage('validate', 'Validating files and request...')
                .addStage('upload', `Uploading ${this.attachedFiles.length} file(s)...`)
                .addStage('analyze', 'Analyzing files with vision AI...')
                .addStage('process', 'Processing with language model...')
                .addStage('finalize', 'Finalizing response...');
        } else {
            progressTracker
                .addStage('validate', 'Validating message...')
                .addStage('connect', 'Connecting to AI model...')
                .addStage('process', 'Generating response...')
                .addStage('finalize', 'Preparing response...');
        }
        
        // Update UI to show loading
        sendButton.disabled = true;
        const sendText = sendButton.querySelector('.send-text');
        const sendLoading = sendButton.querySelector('.send-loading');
        sendText.style.display = 'none';
        sendLoading.style.display = 'inline';
        
        // Start validation stage
        progressTracker.startStage('validate');
        
        // Show loading message for file uploads
        if (this.attachedFiles.length > 0) {
            sendLoading.textContent = `Uploading ${this.attachedFiles.length} file(s)...`;
            this.showNotification(`Processing ${this.attachedFiles.length} file(s), please wait...`, 'info');
            console.log('Set loading state for file upload');
        } else {
            sendLoading.textContent = 'Sending...';
            console.log('Set loading state for text message');
        }

        try {
            console.log('Preparing request...');
            console.log('Conversation ID:', this.conversationId);
            console.log('Model:', this.currentModel);
            
            // Simulate validation delay
            await new Promise(resolve => setTimeout(resolve, 300));
            progressTracker.completeStage('validate', 'Request validated ✓');
            
            // Determine endpoint and request body based on file attachments
            let endpoint, requestBody;
            
            if (this.attachedFiles.length > 0) {
                // Start upload stage
                progressTracker.startStage('upload', `Uploading ${this.attachedFiles.length} file(s)...`);
                
                // Use file chat endpoint
                endpoint = '/api/files/chat-with-files';
                requestBody = {
                    message: message || 'Please analyze these files',
                    files: this.attachedFiles,
                    conversation_id: this.conversationId,
                    model: this.currentModel,
                    vision_model: 'llava:latest',
                    auto_analyze_files: true,
                    max_tokens: 1000,
                    temperature: 0.7
                };
                console.log('Using file chat endpoint with files:', this.attachedFiles.length);
                console.log('Request body size:', JSON.stringify(requestBody).length, 'chars');
                this.showNotification(`Sending message with ${this.attachedFiles.length} file(s)...`, 'info');
                
                // Simulate upload delay
                await new Promise(resolve => setTimeout(resolve, 800));
                progressTracker.completeStage('upload', `${this.attachedFiles.length} file(s) uploaded ✓`);
                progressTracker.startStage('analyze', 'Analyzing files with vision AI...');
            } else {
                // Start connection stage
                progressTracker.startStage('connect', 'Connecting to AI model...');
                
                // Use regular chat endpoint
                endpoint = '/api/chat/message';
                requestBody = {
                    message: message,
                    conversation_id: this.conversationId,
                    model: this.currentModel
                };
                console.log('Using regular chat endpoint');
                
                // Simulate connection delay
                await new Promise(resolve => setTimeout(resolve, 200));
                progressTracker.completeStage('connect', 'Connected to AI model ✓');
            }
            
            const headers = this.getAuthHeaders();
            console.log('Request headers:', headers);
            console.log('Sending to endpoint:', endpoint);
            
            console.log('Making fetch request...');
            
            // Start processing stage
            if (this.attachedFiles.length > 0) {
                progressTracker.completeStage('analyze', 'Files analyzed ✓');
            }
            progressTracker.startStage('process', 'AI model processing...');
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody)
            });
            
            console.log('Response received');
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response body:', errorText);
                progressTracker.errorStage('process', `Server error: ${response.status}`);
                this.showNotification(`Server error: ${response.status} ${response.statusText}`, 'error');
                throw new Error(`HTTP ${response.status}: ${response.statusText}\n${errorText}`);
            }
            
            // Start finalization stage
            progressTracker.completeStage('process', 'Response generated ✓');
            progressTracker.startStage('finalize', 'Preparing response...');
            
            console.log('Parsing response JSON...');
            const data = await response.json();
            console.log('Response data received:', data);
            
            // Simulate finalization delay
            await new Promise(resolve => setTimeout(resolve, 200));
            
            if (data.response) {
                console.log('Adding bot response to chat');
                this.addMessage(data.response, false);
                
                // Display file analysis results if present
                if (data.file_analyses && data.file_analyses.length > 0) {
                    console.log('Displaying file analyses:', data.file_analyses.length);
                    this.displayFileAnalyses(data.file_analyses);
                }
                
                // Process session information if provided
                if (data.session_info) {
                    console.log('Received session info:', data.session_info);
                    this.updateSessionInfo(data.session_info);
                }
                
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
                
                // Clear attached files after successful send
                console.log('Clearing attached files...');
                this.attachedFiles = [];
                this.updateAttachedFilesDisplay();
                
                // Complete progress
                progressTracker.complete('Response completed successfully! ✨');
                this.showNotification('✅ Message sent successfully!', 'success');
                
            } else {
                console.error('No response content in data');
                progressTracker.errorStage('finalize', 'Empty response received');
                this.addMessage('⚠️ Sorry, I received an empty response. Please try again.', false);
            }
            
        } catch (error) {
            console.error('=== SEND MESSAGE ERROR ===');
            console.error('Chat error details:', error);
            console.error('Error stack:', error.stack);
            
            // Update progress tracker with error
            progressTracker.errorStage(progressTracker.currentStageIndex >= 0 ? 
                progressTracker.stages[progressTracker.currentStageIndex].id : 'process', 
                `Error: ${error.message}`);
            
            this.addMessage(`⚠️ Error: ${error.message}. Please try again or check your connection.`, false);
            this.isConnected = false;
            this.updateConnectionStatus();
            this.showNotification(`Error: ${error.message}`, 'error');
            
            // Remove progress tracker after error
            setTimeout(() => {
                progressTracker.remove();
            }, 3000);
            
        } finally {
            console.log('Resetting UI state...');
            // Reset button state
            sendButton.disabled = false;
            const sendText = sendButton.querySelector('.send-text');
            const sendLoading = sendButton.querySelector('.send-loading');
            sendText.style.display = 'inline';
            sendLoading.style.display = 'none';
            sendLoading.textContent = '...';  // Reset loading text
            messageInput.focus();
            console.log('=== SEND MESSAGE END ===');
        }
    }    updateSessionInfo(sessionInfo) {
        console.log('Updating session info:', sessionInfo);
        
        if (sessionInfo.is_guest) {
            // Update guest session state
            this.isGuest = true;
            this.sessionId = sessionInfo.session_id;
            this.guestLimits.maxMessagesPerConversation = sessionInfo.max_messages_per_conversation || 20;
            this.guestLimits.currentConversationMessages = sessionInfo.current_conversation_messages || 0;
            
            // Store session ID in localStorage
            localStorage.setItem('guest_session_id', sessionInfo.session_id);
            
            // Update UI to show guest status
            this.updateUserInterface();
            this.updateGuestLimitDisplay();
            
            console.log('Updated to guest session:', sessionInfo.session_id);
        } else {
            // Update user session state
            this.isGuest = false;
            this.currentUser = {
                username: sessionInfo.username,
                user_id: sessionInfo.user_id
            };
            
            // Update UI to show user status
            this.updateUserInterface();
            
            console.log('Updated to user session:', sessionInfo.username);
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

    displayFileAnalyses(fileAnalyses) {
        console.log('Displaying file analyses:', fileAnalyses);
        
        const messagesContainer = document.getElementById('chat-messages');
        
        fileAnalyses.forEach(analysis => {
            const analysisElement = document.createElement('div');
            analysisElement.className = 'message file-analysis-message';
            
            let analysisContent = `
                <div class="file-analysis-header">
                    <span class="file-icon">${this.getFileIcon(analysis.type)}</span>
                    <span class="file-name">${analysis.filename}</span>
                    <span class="analysis-label">${analysis.type === 'image' ? 'Image Analysis' : 'Document Analysis'}</span>
                </div>
                <div class="file-analysis-content">
                    ${this.formatMessage(analysis.analysis)}
                </div>
            `;
            
            // Add extracted text for documents if available
            if (analysis.extracted_text && analysis.type === 'document') {
                analysisContent += `
                    <div class="extracted-text">
                        <strong>Extracted Text Preview:</strong>
                        <div class="extracted-text-content">${this.formatMessage(analysis.extracted_text)}</div>
                    </div>
                `;
            }
            
            analysisElement.innerHTML = analysisContent;
            messagesContainer.appendChild(analysisElement);
        });
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
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

// Function to return to main page
function returnToMain() {
    console.log('returnToMain() function called');
    try {
        console.log('Attempting to navigate to: /');
        window.location.href = '/';
        console.log('Navigation command sent');
    } catch (error) {
        console.error('Error during navigation:', error);
        alert('Navigation error: ' + error.message);
    }
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
