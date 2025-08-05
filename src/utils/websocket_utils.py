"""
WebSocket Utility Functions
Provides safe WebSocket operations with connection state validation.
"""

import logging
import json
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)

async def safe_websocket_send(websocket: WebSocket, data: dict):
    """
    Safely send data via WebSocket with connection state validation.
    
    Args:
        websocket: The WebSocket connection
        data: Dictionary data to send (will be JSON encoded)
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        # Check WebSocket connection state before sending
        if (websocket and 
            hasattr(websocket, 'client_state') and 
            websocket.client_state == WebSocketState.CONNECTED):
            
            await websocket.send_text(json.dumps(data))
            return True
        else:
            # Don't log as error - client disconnections are normal
            if data.get("type") != "preflight_test":  # Don't spam logs for preflight tests
                logger.debug(f"WebSocket not connected - skipping {data.get('type', 'unknown')} message")
            return False
            
    except Exception as send_error:
        # Only log serious errors, not normal disconnections
        if "close message has been sent" in str(send_error):
            logger.debug(f"WebSocket already closed - skipping {data.get('type', 'unknown')} message")
        else:
            logger.error(f"Failed to send WebSocket message: {send_error}")
        return False
