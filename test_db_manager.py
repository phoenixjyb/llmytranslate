#!/usr/bin/env python3
"""
Direct test of database manager conversation messages.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.services.database_manager import DatabaseManager

def test_db_manager():
    """Test database manager directly."""
    
    print("🔄 Testing DatabaseManager directly...")
    
    db_manager = DatabaseManager()
    
    # Test conversation ID from our debug output
    test_conversation_id = "demo-conv-3-1753722064"
    
    print(f"Testing with conversation ID: {test_conversation_id}")
    
    messages = db_manager.get_conversation_messages(test_conversation_id)
    
    print(f"Found {len(messages)} messages:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
        print(f"      Timestamp: {msg['timestamp']}")
        print(f"      Message ID: {msg['message_id']}")

if __name__ == "__main__":
    test_db_manager()
