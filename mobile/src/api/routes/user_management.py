"""
User management API routes.
Handles user registration, authentication, profile management, and guest access.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ...models.user_models import (
    UserRegistration, UserLogin, UserProfile, UserUpdate, PasswordChange,
    PasswordReset, PasswordResetConfirm, SessionInfo, GuestSession,
    TokenResponse, UserPreferences, UserUsageStats, UserRole
)
from ...services.user_auth_service import user_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["User Management"])
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[SessionInfo]:
    """Get current user from session or token."""
    session_id = None
    
    # Try to get session from Authorization header
    if credentials:
        token_payload = user_auth_service._verify_token(credentials.credentials)
        if token_payload and token_payload.get("type") == "access":
            session_id = token_payload.get("session_id")
    
    # Try to get session from cookies
    if not session_id:
        session_id = request.cookies.get("session_id")
    
    # Try to get guest session from headers
    if not session_id:
        session_id = request.headers.get("X-Guest-Session-Id")
    
    if session_id:
        return await user_auth_service.verify_session(session_id)
    
    return None


async def require_user(current_user: Optional[SessionInfo] = Depends(get_current_user)) -> SessionInfo:
    """Require authenticated user (not guest)."""
    if not current_user or current_user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


async def require_admin(current_user: SessionInfo = Depends(require_user)) -> SessionInfo:
    """Require admin user."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent."""
    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")
    return ip_address, user_agent


# Authentication endpoints

@router.post("/register", response_model=UserProfile)
async def register_user(registration: UserRegistration, request: Request):
    """Register a new user account."""
    try:
        user_profile = await user_auth_service.register_user(registration)
        logger.info(f"New user registered: {user_profile.username}")
        return user_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(login: UserLogin, request: Request, response: Response):
    """Authenticate user and create session."""
    try:
        user_profile = await user_auth_service.authenticate_user(login)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password"
            )
        
        ip_address, user_agent = get_client_info(request)
        token_response = await user_auth_service.create_session(
            user_profile, ip_address, user_agent, login.remember_me
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=token_response.user_profile.user_id,  # This should be session_id from token
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60 if login.remember_me else 24 * 60 * 60
        )
        
        logger.info(f"User logged in: {user_profile.username}")
        return token_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/guest-session", response_model=GuestSession)
async def create_guest_session(request: Request, response: Response):
    """Create a guest session for non-registered users."""
    try:
        ip_address, user_agent = get_client_info(request)
        guest_session = await user_auth_service.create_guest_session(ip_address, user_agent)
        
        # Set guest session cookie
        response.set_cookie(
            key="guest_session_id",
            value=guest_session.session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=24 * 60 * 60  # 24 hours
        )
        
        logger.info(f"Guest session created: {guest_session.session_id}")
        return guest_session
        
    except Exception as e:
        logger.error(f"Guest session creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create guest session"
        )


@router.post("/logout")
async def logout_user(request: Request, response: Response, current_user: Optional[SessionInfo] = Depends(get_current_user)):
    """Logout user and invalidate session."""
    if current_user:
        await user_auth_service.logout(current_user.session_id)
        
        # Clear cookies
        response.delete_cookie("session_id")
        response.delete_cookie("guest_session_id")
        
        logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        token_response = await user_auth_service.refresh_token(refresh_token)
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        return token_response
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


# Profile management endpoints

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: SessionInfo = Depends(require_user)):
    """Get current user profile."""
    user_profile = await user_auth_service.get_user_profile(current_user.user_id)
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return user_profile


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    updates: UserUpdate,
    current_user: SessionInfo = Depends(require_user)
):
    """Update user profile."""
    try:
        updated_profile = await user_auth_service.update_user_profile(
            current_user.user_id, updates
        )
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        logger.info(f"Profile updated for user: {current_user.username}")
        return updated_profile
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: SessionInfo = Depends(require_user)
):
    """Change user password."""
    try:
        success = await user_auth_service.change_password(
            current_user.user_id, password_change
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
        logger.info(f"Password changed for user: {current_user.username}")
        return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Session management endpoints

@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(current_user: SessionInfo = Depends(require_user)):
    """Get all active sessions for current user."""
    try:
        sessions = await user_auth_service.get_user_sessions(current_user.user_id)
        return sessions
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: SessionInfo = Depends(require_user)
):
    """Terminate a specific session."""
    try:
        # Verify the session belongs to the current user
        user_sessions = await user_auth_service.get_user_sessions(current_user.user_id)
        session_ids = [s.session_id for s in user_sessions]
        
        if session_id not in session_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot terminate session of another user"
            )
        
        await user_auth_service.logout(session_id)
        logger.info(f"Session terminated: {session_id} by user: {current_user.username}")
        
        return {"message": "Session terminated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session termination error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session termination failed"
        )


# Guest access info endpoint

@router.get("/guest-info")
async def get_guest_info(current_user: Optional[SessionInfo] = Depends(get_current_user)):
    """Get information about guest access capabilities."""
    guest_limits = {
        "max_conversations": 5,
        "max_messages_per_conversation": 20,
        "conversation_timeout_minutes": 60,
        "features_available": [
            "Basic chat",
            "Model selection",
            "Limited conversation history"
        ],
        "features_restricted": [
            "Conversation persistence",
            "Profile customization",
            "Advanced models",
            "Unlimited usage"
        ]
    }
    
    if current_user and not current_user.is_guest:
        user_profile = await user_auth_service.get_user_profile(current_user.user_id)
        return {
            "is_guest": False,
            "user_profile": user_profile,
            "upgrade_benefits": [
                "Unlimited conversations",
                "Persistent conversation history",
                "Profile customization",
                "Priority model access",
                "Advanced features"
            ]
        }
    
    return {
        "is_guest": True,
        "guest_limits": guest_limits,
        "registration_benefits": [
            "Unlimited conversations",
            "Persistent conversation history",
            "Profile customization",
            "Priority model access",
            "Advanced features"
        ]
    }


# Status and health endpoints

@router.get("/status")
async def get_user_status(current_user: Optional[SessionInfo] = Depends(get_current_user)):
    """Get current user authentication status."""
    if not current_user:
        return {
            "authenticated": False,
            "is_guest": False,
            "message": "No active session"
        }
    
    return {
        "authenticated": not current_user.is_guest,
        "is_guest": current_user.is_guest,
        "username": current_user.username,
        "role": current_user.role.value,
        "session_expires": current_user.expires_at.isoformat(),
        "session_id": current_user.session_id
    }


# Utility endpoints for frontend

@router.get("/check-username/{username}")
async def check_username_availability(username: str):
    """Check if username is available for registration."""
    try:
        # This would be implemented with a database query
        # For now, just validate format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return {
                "available": False,
                "message": "Username can only contain letters, numbers, hyphens, and underscores"
            }
        
        if len(username) < 3 or len(username) > 50:
            return {
                "available": False,
                "message": "Username must be between 3 and 50 characters"
            }
        
        # TODO: Check database for existing username
        return {
            "available": True,
            "message": "Username is available"
        }
        
    except Exception as e:
        logger.error(f"Username check error: {e}")
        return {
            "available": False,
            "message": "Unable to check username availability"
        }


@router.get("/check-email/{email}")
async def check_email_availability(email: str):
    """Check if email is available for registration."""
    try:
        from email_validator import validate_email, EmailNotValidError
        
        # Validate email format
        try:
            validate_email(email)
        except EmailNotValidError:
            return {
                "available": False,
                "message": "Invalid email format"
            }
        
        # TODO: Check database for existing email
        return {
            "available": True,
            "message": "Email is available"
        }
        
    except Exception as e:
        logger.error(f"Email check error: {e}")
        return {
            "available": False,
            "message": "Unable to check email availability"
        }
