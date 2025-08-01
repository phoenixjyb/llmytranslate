"""
User authentication and management service.
Handles user registration, login, session management, and guest access.
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from passlib.context import CryptContext
from email_validator import validate_email, EmailNotValidError
import sqlite3
import json
import logging
from pathlib import Path

from ..models.user_models import (
    UserRegistration, UserLogin, UserProfile, UserUpdate, PasswordChange,
    PasswordReset, PasswordResetConfirm, SessionInfo, GuestSession,
    TokenResponse, UserPreferences, UserUsageStats, UserRole, UserStatus,
    AdminUserView
)

logger = logging.getLogger(__name__)


class UserAuthService:
    """
    Comprehensive user authentication and management service.
    Supports both traditional user accounts and guest access.
    """
    
    def __init__(self, database_path: str = "users.db", secret_key: str = "your-secret-key"):
        self.database_path = Path(database_path)
        self.secret_key = secret_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.guest_session_expire_hours = 24
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with user tables."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT 'user',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    email_verified BOOLEAN DEFAULT FALSE,
                    email_verification_token TEXT,
                    password_reset_token TEXT,
                    password_reset_expires TIMESTAMP,
                    avatar_url TEXT,
                    timezone TEXT DEFAULT 'UTC',
                    language TEXT DEFAULT 'en',
                    preferences TEXT DEFAULT '{}',
                    usage_stats TEXT DEFAULT '{}',
                    total_logins INTEGER DEFAULT 0,
                    failed_login_attempts INTEGER DEFAULT 0
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_guest BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    refresh_token_hash TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)")
            
            conn.commit()
            logger.info("User database initialized successfully")
    
    def _hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt."""
        salt = secrets.token_hex(32)
        password_hash = self.pwd_context.hash(password + salt)
        return password_hash, salt
    
    def _verify_password(self, password: str, salt: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(password + salt, password_hash)
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def register_user(self, registration: UserRegistration) -> UserProfile:
        """Register a new user."""
        try:
            # Basic email format validation (less strict for development)
            if "@" not in registration.email or "." not in registration.email.split("@")[1]:
                raise ValueError("Invalid email format")
        except Exception as e:
            if "Invalid email" not in str(e):
                raise ValueError(f"Invalid email: {str(e)}")
        
        user_id = self._generate_user_id()
        password_hash, salt = self._hash_password(registration.password)
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE username = ? OR email = ?",
                (registration.username.lower(), registration.email.lower())
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError("Username or email already exists")
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, email, password_hash, salt,
                    first_name, last_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, registration.username.lower(), registration.email.lower(),
                password_hash, salt, registration.first_name, registration.last_name,
                datetime.utcnow(), datetime.utcnow()
            ))
            
            conn.commit()
            logger.info(f"New user registered: {registration.username}")
            
            # Return user profile
            return await self.get_user_profile(user_id)
    
    async def authenticate_user(self, login: UserLogin) -> Optional[UserProfile]:
        """Authenticate user and return profile if successful."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Find user by username or email
            cursor.execute("""
                SELECT user_id, username, email, password_hash, salt, status, failed_login_attempts
                FROM users 
                WHERE username = ? OR email = ?
            """, (login.username_or_email.lower(), login.username_or_email.lower()))
            
            user_data = cursor.fetchone()
            if not user_data:
                return None
            
            user_id, username, email, password_hash, salt, status, failed_attempts = user_data
            
            # Check account status
            if status != UserStatus.ACTIVE.value:
                raise ValueError(f"Account is {status}")
            
            # Check for too many failed attempts
            if failed_attempts >= 5:
                raise ValueError("Account temporarily locked due to too many failed login attempts")
            
            # Verify password
            if not self._verify_password(login.password, salt, password_hash):
                # Increment failed attempts
                cursor.execute(
                    "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return None
            
            # Reset failed attempts and update last login
            cursor.execute("""
                UPDATE users SET 
                    failed_login_attempts = 0,
                    last_login = ?,
                    total_logins = total_logins + 1
                WHERE user_id = ?
            """, (datetime.utcnow(), user_id))
            
            conn.commit()
            logger.info(f"User authenticated: {username}")
            
            return await self.get_user_profile(user_id)
    
    async def create_session(self, user_profile: UserProfile, ip_address: str = None, 
                           user_agent: str = None, remember_me: bool = False) -> TokenResponse:
        """Create a new user session with tokens."""
        session_id = secrets.token_urlsafe(32)
        
        # Set expiration times
        access_expire = timedelta(minutes=self.access_token_expire_minutes)
        refresh_expire = timedelta(days=self.refresh_token_expire_days if remember_me else 1)
        
        # Create tokens
        access_token_data = {
            "sub": user_profile.user_id,
            "username": user_profile.username,
            "role": user_profile.role.value,
            "session_id": session_id,
            "type": "access"
        }
        access_token = self._generate_token(access_token_data, access_expire)
        
        refresh_token_data = {
            "sub": user_profile.user_id,
            "session_id": session_id,
            "type": "refresh"
        }
        refresh_token = self._generate_token(refresh_token_data, refresh_expire)
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Store session in database
        expires_at = datetime.utcnow() + refresh_expire
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, user_id, expires_at, ip_address, user_agent,
                    is_guest, refresh_token_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, user_profile.user_id, expires_at, ip_address, user_agent, False, refresh_token_hash))
            
            conn.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_expire.total_seconds()),
            user_profile=user_profile
        )
    
    async def create_guest_session(self, ip_address: str = None, user_agent: str = None) -> GuestSession:
        """Create a guest session for non-registered users."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.guest_session_expire_hours)
        
        guest_session = GuestSession(
            session_id=session_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store guest session
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, expires_at, ip_address, user_agent, is_guest
                ) VALUES (?, ?, ?, ?, ?)
            """, (session_id, expires_at, ip_address, user_agent, True))
            
            conn.commit()
        
        logger.info(f"Guest session created: {session_id}")
        return guest_session
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, email, first_name, last_name, role, status,
                       created_at, last_login, email_verified, avatar_url, timezone,
                       language, preferences, usage_stats
                FROM users WHERE user_id = ?
            """, (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return None
            
            # Parse JSON fields
            preferences = json.loads(user_data[13] or '{}')
            usage_stats = json.loads(user_data[14] or '{}')
            
            # Get conversation counts (optional, handle gracefully if table doesn't exist)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM conversation_metadata WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                total_conversations = result[0] if result else 0
            except:
                # Table might not exist yet, set to 0
                total_conversations = 0
            
            return UserProfile(
                user_id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                first_name=user_data[3],
                last_name=user_data[4],
                role=UserRole(user_data[5]),
                status=UserStatus(user_data[6]),
                created_at=datetime.fromisoformat(user_data[7]),
                last_login=datetime.fromisoformat(user_data[8]) if user_data[8] else None,
                email_verified=bool(user_data[9]),
                avatar_url=user_data[10],
                timezone=user_data[11],
                language=user_data[12],
                total_conversations=total_conversations,
                total_messages=usage_stats.get('total_messages', 0),
                last_activity=datetime.fromisoformat(usage_stats.get('last_activity')) if usage_stats.get('last_activity') else None
            )
    
    async def verify_session(self, session_id: str) -> Optional[SessionInfo]:
        """Verify session and return session info."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.session_id, s.user_id, u.username, u.role, s.created_at,
                       s.expires_at, s.ip_address, s.user_agent, s.is_guest
                FROM sessions s
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.session_id = ? AND s.is_active = TRUE AND s.expires_at > ?
            """, (session_id, datetime.utcnow()))
            
            session_data = cursor.fetchone()
            if not session_data:
                return None
            
            return SessionInfo(
                session_id=session_data[0],
                user_id=session_data[1] or "guest",
                username=session_data[2] or "Guest",
                role=UserRole(session_data[3]) if session_data[3] else UserRole.GUEST,
                created_at=datetime.fromisoformat(session_data[4]),
                expires_at=datetime.fromisoformat(session_data[5]),
                ip_address=session_data[6],
                user_agent=session_data[7],
                is_guest=bool(session_data[8])
            )
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresh access token using refresh token."""
        payload = self._verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id or not session_id:
            return None
        
        # Verify refresh token hash in database
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM sessions 
                WHERE session_id = ? AND refresh_token_hash = ? AND is_active = TRUE AND expires_at > ?
            """, (session_id, refresh_token_hash, datetime.utcnow()))
            
            if not cursor.fetchone():
                return None
        
        # Get user profile and create new session
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            return None
        
        return await self.create_session(user_profile)
    
    async def logout(self, session_id: str):
        """Logout user and invalidate session."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET is_active = FALSE WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
        
        logger.info(f"Session logged out: {session_id}")
    
    async def update_user_profile(self, user_id: str, updates: UserUpdate) -> Optional[UserProfile]:
        """Update user profile."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            update_fields = []
            update_values = []
            
            if updates.first_name is not None:
                update_fields.append("first_name = ?")
                update_values.append(updates.first_name)
            
            if updates.last_name is not None:
                update_fields.append("last_name = ?")
                update_values.append(updates.last_name)
            
            if updates.timezone is not None:
                update_fields.append("timezone = ?")
                update_values.append(updates.timezone)
            
            if updates.language is not None:
                update_fields.append("language = ?")
                update_values.append(updates.language)
            
            if updates.avatar_url is not None:
                update_fields.append("avatar_url = ?")
                update_values.append(updates.avatar_url)
            
            if update_fields:
                update_fields.append("updated_at = ?")
                update_values.append(datetime.utcnow())
                update_values.append(user_id)
                
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
                cursor.execute(query, update_values)
                conn.commit()
        
        return await self.get_user_profile(user_id)
    
    async def change_password(self, user_id: str, password_change: PasswordChange) -> bool:
        """Change user password."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Get current password info
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE user_id = ?",
                (user_id,)
            )
            user_data = cursor.fetchone()
            if not user_data:
                return False
            
            current_hash, salt = user_data
            
            # Verify current password
            if not self._verify_password(password_change.current_password, salt, current_hash):
                raise ValueError("Current password is incorrect")
            
            # Hash new password
            new_hash, new_salt = self._hash_password(password_change.new_password)
            
            # Update password
            cursor.execute("""
                UPDATE users SET password_hash = ?, salt = ?, updated_at = ?
                WHERE user_id = ?
            """, (new_hash, new_salt, datetime.utcnow(), user_id))
            
            conn.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        return True
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM sessions WHERE expires_at < ?",
                (datetime.utcnow(),)
            )
            deleted_count = cursor.rowcount
            conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired sessions")
    
    async def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, user_id, created_at, expires_at, ip_address, user_agent, is_guest
                FROM sessions 
                WHERE user_id = ? AND is_active = TRUE AND expires_at > ?
                ORDER BY created_at DESC
            """, (user_id, datetime.utcnow()))
            
            sessions = []
            for row in cursor.fetchall():
                user_profile = await self.get_user_profile(user_id)
                sessions.append(SessionInfo(
                    session_id=row[0],
                    user_id=row[1],
                    username=user_profile.username if user_profile else "Unknown",
                    role=user_profile.role if user_profile else UserRole.USER,
                    created_at=datetime.fromisoformat(row[2]),
                    expires_at=datetime.fromisoformat(row[3]),
                    ip_address=row[4],
                    user_agent=row[5],
                    is_guest=bool(row[6])
                ))
            
            return sessions


# Global instance
user_auth_service = UserAuthService()
