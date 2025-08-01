"""
User account management models for traditional authentication system.
Supports both registered users and guest access.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import re


class UserRole(str, Enum):
    """User roles for permissions."""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class UserRegistration(BaseModel):
    """User registration model."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    """User login model."""
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Keep user logged in")


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Account status")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    email_verified: bool = Field(default=False, description="Email verification status")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    timezone: Optional[str] = Field(default="UTC", description="User timezone")
    language: Optional[str] = Field(default="en", description="Preferred language")
    
    # Usage statistics
    total_conversations: int = Field(default=0, description="Total conversations created")
    total_messages: int = Field(default=0, description="Total messages sent")
    last_activity: Optional[datetime] = Field(None, description="Last activity time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserUpdate(BaseModel):
    """User profile update model."""
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None)
    language: Optional[str] = Field(None)
    avatar_url: Optional[str] = Field(None)


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class PasswordReset(BaseModel):
    """Password reset request model."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class SessionInfo(BaseModel):
    """User session information."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    role: UserRole = Field(..., description="User role")
    created_at: datetime = Field(..., description="Session creation time")
    expires_at: datetime = Field(..., description="Session expiration time")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    is_guest: bool = Field(default=False, description="Whether this is a guest session")


class GuestSession(BaseModel):
    """Guest session model for non-registered users."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Guest session ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    expires_at: datetime = Field(..., description="Session expiration time")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    
    # Guest limitations
    max_conversations: int = Field(default=5, description="Maximum conversations for guests")
    max_messages_per_conversation: int = Field(default=20, description="Maximum messages per conversation")
    conversation_timeout_minutes: int = Field(default=60, description="Conversation timeout in minutes")


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_profile: UserProfile = Field(..., description="User profile information")


class UserPreferences(BaseModel):
    """User preferences for chat and translation."""
    preferred_model: str = Field(default="gemma3:latest", description="Default AI model")
    default_language: str = Field(default="en", description="Default language for translations")
    chat_theme: str = Field(default="light", description="Chat interface theme")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    auto_save_conversations: bool = Field(default=True, description="Auto-save conversations")
    conversation_history_limit: int = Field(default=50, description="Number of conversations to keep")
    
    # Privacy settings
    share_usage_data: bool = Field(default=False, description="Share usage data for improvements")
    public_profile: bool = Field(default=False, description="Make profile publicly visible")


class UserUsageStats(BaseModel):
    """User usage statistics."""
    user_id: str = Field(..., description="User identifier")
    current_period_start: datetime = Field(..., description="Current billing/usage period start")
    
    # Usage counters
    conversations_count: int = Field(default=0, description="Conversations this period")
    messages_count: int = Field(default=0, description="Messages this period")
    translations_count: int = Field(default=0, description="Translations this period")
    tokens_used: int = Field(default=0, description="Tokens consumed this period")
    
    # Limits based on user role
    max_conversations: int = Field(default=100, description="Maximum conversations allowed")
    max_messages: int = Field(default=1000, description="Maximum messages allowed")
    max_translations: int = Field(default=500, description="Maximum translations allowed")
    max_tokens: int = Field(default=100000, description="Maximum tokens allowed")
    
    # Reset information
    resets_at: datetime = Field(..., description="When usage counters reset")
    

class AdminUserView(BaseModel):
    """Admin view of user information."""
    user_id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime]
    email_verified: bool
    
    # Extended admin information
    ip_addresses: List[str] = Field(default=[], description="Recent IP addresses")
    total_logins: int = Field(default=0, description="Total login count")
    failed_login_attempts: int = Field(default=0, description="Recent failed login attempts")
    
    # Usage summary
    usage_stats: UserUsageStats
    active_sessions: int = Field(default=0, description="Current active sessions")
    last_activity: Optional[datetime] = Field(None, description="Last activity time")


# Database models (for SQLAlchemy or similar ORM)
class UserDBModel:
    """Database model for users (reference for ORM implementation)."""
    
    # This would be implemented with your chosen ORM
    # Example fields that would be in the database:
    
    # id: Primary key
    # user_id: UUID string
    # username: Unique string
    # email: Unique string
    # password_hash: String (hashed password)
    # salt: String (password salt)
    # first_name: Optional string
    # last_name: Optional string
    # role: Enum string
    # status: Enum string
    # created_at: Timestamp
    # updated_at: Timestamp
    # last_login: Optional timestamp
    # email_verified: Boolean
    # email_verification_token: Optional string
    # password_reset_token: Optional string
    # password_reset_expires: Optional timestamp
    # avatar_url: Optional string
    # timezone: String
    # language: String
    # preferences: JSON field
    # usage_stats: JSON field
    pass


class SessionDBModel:
    """Database model for user sessions (reference for ORM implementation)."""
    
    # This would be implemented with your chosen ORM
    # Example fields:
    
    # id: Primary key
    # session_id: UUID string
    # user_id: Foreign key to users table
    # created_at: Timestamp
    # expires_at: Timestamp
    # ip_address: Optional string
    # user_agent: Optional string
    # is_guest: Boolean
    # refresh_token_hash: Optional string
    # is_active: Boolean
    pass
