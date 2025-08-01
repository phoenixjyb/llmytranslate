"""
Authentication service for API key validation and signature verification.
"""

import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.config import get_settings
from ..models.schemas import APIKeyInfo

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()


class AuthService:
    """Authentication service for API key validation and Baidu-compatible signature verification."""
    
    def __init__(self):
        self.settings = get_settings()
        
        # In-memory API key storage for demo
        # In production, this should use a proper database
        self.api_keys: Dict[str, APIKeyInfo] = {}
        
        # Add default demo API key
        self._add_demo_api_key()
    
    def _add_demo_api_key(self) -> None:
        """Add a demo API key for testing."""
        demo_key = APIKeyInfo(
            app_id="demo_app_id",
            app_secret="demo_app_secret",
            name="Demo API Key",
            is_active=True,
            rate_limit_per_minute=60,
            rate_limit_per_hour=1000,
            rate_limit_per_day=10000,
            created_at=datetime.utcnow(),
            last_used_at=None
        )
        self.api_keys[demo_key.app_id] = demo_key
        logger.info("Added demo API key", app_id=demo_key.app_id)
    
    async def validate_request(
        self,
        app_id: str,
        query_text: str,
        from_lang: str,
        to_lang: str,
        salt: str,
        sign: str
    ) -> Dict[str, Any]:
        """
        Validate API request with Baidu-compatible signature verification.
        
        Baidu signature format: MD5(appid + query + salt + secret)
        """
        try:
            # Check if API key exists
            api_key_info = self.api_keys.get(app_id)
            if not api_key_info:
                return {
                    "valid": False,
                    "error_code": "INVALID_APP_ID",
                    "error_msg": "Invalid application ID"
                }
            
            # Check if API key is active
            if not api_key_info.is_active:
                return {
                    "valid": False,
                    "error_code": "INACTIVE_APP_ID",
                    "error_msg": "Application ID is inactive"
                }
            
            # Verify signature (skip if disabled in development)
            if not self.settings.auth.disable_signature_validation:
                if not self._verify_signature(
                    app_id=app_id,
                    query=query_text,
                    salt=salt,
                    secret=api_key_info.app_secret,
                    provided_sign=sign
                ):
                    return {
                        "valid": False,
                        "error_code": "INVALID_SIGNATURE",
                        "error_msg": "Invalid signature"
                    }
            else:
                logger.info("Signature validation disabled for development")
            
            # Update last used timestamp
            api_key_info.last_used_at = datetime.utcnow()
            
            logger.info(
                "API request validated successfully",
                app_id=app_id,
                from_lang=from_lang,
                to_lang=to_lang
            )
            
            return {
                "valid": True,
                "api_key_info": api_key_info
            }
            
        except Exception as e:
            logger.error("Authentication validation failed", error=str(e))
            return {
                "valid": False,
                "error_code": "AUTH_ERROR",
                "error_msg": f"Authentication error: {str(e)}"
            }
    
    def _verify_signature(
        self,
        app_id: str,
        query: str,
        salt: str,
        secret: str,
        provided_sign: str
    ) -> bool:
        """
        Verify signature using Baidu translation API format.
        
        Signature calculation: MD5(appid + query + salt + secret)
        """
        try:
            # Create signature string
            sign_str = f"{app_id}{query}{salt}{secret}"
            
            # Calculate MD5 hash
            calculated_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
            
            # Compare signatures (case-insensitive)
            is_valid = calculated_sign.lower() == provided_sign.lower()
            
            if not is_valid:
                logger.warning(
                    "Signature mismatch",
                    app_id=app_id,
                    calculated=calculated_sign,
                    provided=provided_sign
                )
            
            return is_valid
            
        except Exception as e:
            logger.error("Signature verification failed", error=str(e))
            return False
    
    def create_signature(
        self,
        app_id: str,
        query: str,
        salt: str,
        secret: str
    ) -> str:
        """
        Create signature for testing purposes.
        
        This method can be used by clients to generate proper signatures.
        """
        sign_str = f"{app_id}{query}{salt}{secret}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    async def add_api_key(self, api_key_info: APIKeyInfo) -> bool:
        """Add a new API key."""
        try:
            if api_key_info.app_id in self.api_keys:
                logger.warning("API key already exists", app_id=api_key_info.app_id)
                return False
            
            self.api_keys[api_key_info.app_id] = api_key_info
            logger.info("API key added", app_id=api_key_info.app_id, name=api_key_info.name)
            return True
            
        except Exception as e:
            logger.error("Failed to add API key", error=str(e))
            return False
    
    async def update_api_key(self, app_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing API key."""
        try:
            if app_id not in self.api_keys:
                logger.warning("API key not found for update", app_id=app_id)
                return False
            
            api_key_info = self.api_keys[app_id]
            
            # Update allowed fields
            allowed_fields = {
                'name', 'is_active', 'rate_limit_per_minute',
                'rate_limit_per_hour', 'rate_limit_per_day'
            }
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(api_key_info, field):
                    setattr(api_key_info, field, value)
            
            logger.info("API key updated", app_id=app_id, updates=list(updates.keys()))
            return True
            
        except Exception as e:
            logger.error("Failed to update API key", app_id=app_id, error=str(e))
            return False
    
    async def delete_api_key(self, app_id: str) -> bool:
        """Delete an API key."""
        try:
            if app_id not in self.api_keys:
                logger.warning("API key not found for deletion", app_id=app_id)
                return False
            
            del self.api_keys[app_id]
            logger.info("API key deleted", app_id=app_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete API key", app_id=app_id, error=str(e))
            return False
    
    async def get_api_key(self, app_id: str) -> Optional[APIKeyInfo]:
        """Get API key information."""
        return self.api_keys.get(app_id)
    
    async def list_api_keys(self) -> Dict[str, APIKeyInfo]:
        """List all API keys."""
        return self.api_keys.copy()
    
    async def get_rate_limits(self, app_id: str) -> Optional[Dict[str, int]]:
        """Get rate limits for an API key."""
        api_key_info = self.api_keys.get(app_id)
        if not api_key_info:
            return None
        
        return {
            "per_minute": api_key_info.rate_limit_per_minute,
            "per_hour": api_key_info.rate_limit_per_hour,
            "per_day": api_key_info.rate_limit_per_day
        }
    
    def generate_demo_request(self, query: str, from_lang: str = "en", to_lang: str = "zh") -> Dict[str, str]:
        """
        Generate a demo request with proper signature for testing.
        """
        app_id = "demo_app_id"
        secret = "demo_app_secret"
        salt = str(int(datetime.utcnow().timestamp() * 1000))  # Use timestamp as salt
        
        signature = self.create_signature(app_id, query, salt, secret)
        
        return {
            "q": query,
            "from": from_lang,
            "to": to_lang,
            "appid": app_id,
            "salt": salt,
            "sign": signature
        }


# Global auth service instance
auth_service = AuthService()
