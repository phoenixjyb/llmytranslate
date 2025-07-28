// User Authentication JavaScript
class UserAuth {
    constructor() {
        this.apiBase = '/api/users';
        this.currentUser = null;
        this.isGuest = false;
        this.sessionId = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkExistingSession();
        this.setupPasswordStrength();
        this.setupUsernameValidation();
        this.setupEmailValidation();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Form submissions
        document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('register-form').addEventListener('submit', (e) => this.handleRegister(e));

        // Guest access buttons
        document.getElementById('guest-access-button').addEventListener('click', () => this.createGuestSession());
        document.getElementById('guest-access-button-2').addEventListener('click', () => this.createGuestSession());
    }

    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update form visibility
        document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
        document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');

        // Clear any error messages
        this.clearErrorMessages();
    }

    async checkExistingSession() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            if (response.ok) {
                const status = await response.json();
                if (status.authenticated || status.is_guest) {
                    // User is already logged in, redirect to chat
                    this.redirectToChat();
                }
            }
        } catch (error) {
            console.log('No existing session found');
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const button = document.getElementById('login-button');
        const text = document.getElementById('login-text');
        const loading = document.getElementById('login-loading');
        
        // Show loading state
        button.disabled = true;
        text.classList.add('hidden');
        loading.classList.remove('hidden');
        
        try {
            const formData = {
                username_or_email: document.getElementById('login-email').value.trim(),
                password: document.getElementById('login-password').value,
                remember_me: document.getElementById('remember-me').checked
            };

            const response = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            // Store authentication info
            this.currentUser = data.user_profile;
            this.sessionId = data.user_profile.user_id; // This should be session_id from response
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            // Redirect to chat
            this.redirectToChat();

        } catch (error) {
            this.showError('login-password-error', error.message);
        } finally {
            // Reset button state
            button.disabled = false;
            text.classList.remove('hidden');
            loading.classList.add('hidden');
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        
        const button = document.getElementById('register-button');
        const text = document.getElementById('register-text');
        const loading = document.getElementById('register-loading');
        
        // Show loading state
        button.disabled = true;
        text.classList.add('hidden');
        loading.classList.remove('hidden');
        
        try {
            const formData = {
                username: document.getElementById('register-username').value.trim(),
                email: document.getElementById('register-email').value.trim(),
                password: document.getElementById('register-password').value,
                first_name: document.getElementById('register-first-name').value.trim() || null,
                last_name: document.getElementById('register-last-name').value.trim() || null
            };

            // Client-side validation
            if (!this.validateRegistrationForm(formData)) {
                return;
            }

            const response = await fetch(`${this.apiBase}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            // Auto-login after successful registration
            const loginData = {
                username_or_email: formData.username,
                password: formData.password,
                remember_me: true
            };

            const loginResponse = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData)
            });

            const loginResult = await loginResponse.json();

            if (loginResponse.ok) {
                // Store authentication info
                this.currentUser = loginResult.user_profile;
                this.sessionId = loginResult.user_profile.user_id;
                localStorage.setItem('auth_token', loginResult.access_token);
                localStorage.setItem('refresh_token', loginResult.refresh_token);

                // Redirect to chat
                this.redirectToChat();
            } else {
                // Registration successful but auto-login failed, switch to login tab
                this.switchTab('login');
                this.showSuccess('login-email-error', 'Registration successful! Please log in.');
            }

        } catch (error) {
            this.showError('register-password-error', error.message);
        } finally {
            // Reset button state
            button.disabled = false;
            text.classList.remove('hidden');
            loading.classList.add('hidden');
        }
    }

    async createGuestSession() {
        try {
            const response = await fetch(`${this.apiBase}/guest-session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to create guest session');
            }

            // Store guest session info
            this.isGuest = true;
            this.sessionId = data.session_id;
            localStorage.setItem('guest_session_id', data.session_id);

            // Redirect to chat
            this.redirectToChat();

        } catch (error) {
            console.error('Guest session creation failed:', error);
            alert('Failed to create guest session. Please try again.');
        }
    }

    validateRegistrationForm(formData) {
        let isValid = true;

        // Clear previous errors
        this.clearErrorMessages();

        // Username validation
        if (!formData.username || formData.username.length < 3) {
            this.showError('register-username-error', 'Username must be at least 3 characters long');
            isValid = false;
        } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
            this.showError('register-username-error', 'Username can only contain letters, numbers, hyphens, and underscores');
            isValid = false;
        }

        // Email validation
        if (!formData.email || !this.isValidEmail(formData.email)) {
            this.showError('register-email-error', 'Please enter a valid email address');
            isValid = false;
        }

        // Password validation
        const passwordStrength = this.checkPasswordStrength(formData.password);
        if (passwordStrength.score < 2) {
            this.showError('register-password-error', 'Password is too weak. Please use a stronger password.');
            isValid = false;
        }

        return isValid;
    }

    setupPasswordStrength() {
        const passwordInput = document.getElementById('register-password');
        const strengthBar = document.getElementById('password-strength-bar');

        passwordInput.addEventListener('input', (e) => {
            const password = e.target.value;
            const strength = this.checkPasswordStrength(password);
            
            strengthBar.style.width = `${(strength.score + 1) * 25}%`;
            strengthBar.className = `password-strength-bar strength-${strength.level}`;
        });
    }

    checkPasswordStrength(password) {
        let score = 0;
        let level = 'weak';

        if (password.length >= 8) score++;
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/\d/.test(password)) score++;
        if (/[^a-zA-Z\d]/.test(password)) score++;

        if (score >= 4) level = 'strong';
        else if (score >= 3) level = 'good';
        else if (score >= 2) level = 'fair';

        return { score, level };
    }

    setupUsernameValidation() {
        const usernameInput = document.getElementById('register-username');
        let validationTimeout;

        usernameInput.addEventListener('input', (e) => {
            clearTimeout(validationTimeout);
            const username = e.target.value.trim();

            if (username.length >= 3) {
                validationTimeout = setTimeout(() => {
                    this.checkUsernameAvailability(username);
                }, 500);
            }
        });
    }

    setupEmailValidation() {
        const emailInput = document.getElementById('register-email');
        let validationTimeout;

        emailInput.addEventListener('input', (e) => {
            clearTimeout(validationTimeout);
            const email = e.target.value.trim();

            if (this.isValidEmail(email)) {
                validationTimeout = setTimeout(() => {
                    this.checkEmailAvailability(email);
                }, 500);
            }
        });
    }

    async checkUsernameAvailability(username) {
        try {
            const response = await fetch(`${this.apiBase}/check-username/${encodeURIComponent(username)}`);
            const data = await response.json();

            const errorElement = document.getElementById('register-username-error');
            const successElement = document.getElementById('register-username-success');

            if (data.available) {
                errorElement.textContent = '';
                successElement.textContent = '✓ Username is available';
            } else {
                successElement.textContent = '';
                errorElement.textContent = data.message;
            }
        } catch (error) {
            console.error('Username check failed:', error);
        }
    }

    async checkEmailAvailability(email) {
        try {
            const response = await fetch(`${this.apiBase}/check-email/${encodeURIComponent(email)}`);
            const data = await response.json();

            const errorElement = document.getElementById('register-email-error');
            const successElement = document.getElementById('register-email-success');

            if (data.available) {
                errorElement.textContent = '';
                successElement.textContent = '✓ Email is available';
            } else {
                successElement.textContent = '';
                errorElement.textContent = data.message;
            }
        } catch (error) {
            console.error('Email check failed:', error);
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.previousElementSibling?.classList.add('error');
        }
    }

    showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('error-message');
            element.classList.add('success-message');
        }
    }

    clearErrorMessages() {
        document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
        document.querySelectorAll('.success-message').forEach(el => el.textContent = '');
        document.querySelectorAll('.form-input').forEach(el => el.classList.remove('error'));
    }

    redirectToChat() {
        // Redirect to chat interface
        window.location.href = '/chat';
    }

    // Utility method for getting auth headers
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

    // Method to check if user is authenticated
    isAuthenticated() {
        return !!(this.currentUser && !this.isGuest);
    }

    // Method to logout
    async logout() {
        try {
            await fetch(`${this.apiBase}/logout`, {
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

        // Reset state
        this.currentUser = null;
        this.isGuest = false;
        this.sessionId = null;

        // Redirect to auth page
        window.location.href = '/auth.html';
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.userAuth = new UserAuth();
});
