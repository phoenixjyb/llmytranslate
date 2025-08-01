#!/usr/bin/env python3
"""
Debug conversation data in the database.
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def debug_conversations():
    """Debug conversation data in the database."""
    
    db_path = "data/llmytranslate.db"
    
    print("🔍 Debugging conversation data in database...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check conversation metadata
        print("\n📋 Conversation Metadata:")
        cursor.execute("SELECT conversation_id, user_id, title, message_count, created_at FROM conversation_metadata ORDER BY created_at DESC")
        conversations = cursor.fetchall()
        
        if conversations:
            for conv in conversations:
                conv_id, user_id, title, msg_count, created = conv
                print(f"  - ID: {conv_id}")
                print(f"    User: {user_id}")
                print(f"    Title: {title}")
                print(f"    Messages: {msg_count}")
                print(f"    Created: {created}")
                print()
        else:
            print("  No conversations found in database")
        
        # Check conversation messages
        print("💬 Conversation Messages:")
        cursor.execute("SELECT conversation_id, role, content, timestamp FROM conversation_messages ORDER BY timestamp DESC LIMIT 10")
        messages = cursor.fetchall()
        
        if messages:
            for msg in messages:
                conv_id, role, content, timestamp = msg
                content_preview = content[:50] + "..." if len(content) > 50 else content
                print(f"  - {conv_id}: {role} - {content_preview} ({timestamp})")
        else:
            print("  No messages found in database")
        
        # Check specific conversation that failed
        print("\n🔎 Checking specific conversation messages:")
        if conversations:
            test_conv_id = conversations[0][0]  # First conversation ID
            print(f"Looking for messages in conversation: {test_conv_id}")
            
            cursor.execute("SELECT message_id, role, content, timestamp FROM conversation_messages WHERE conversation_id = ? ORDER BY timestamp", (test_conv_id,))
            specific_messages = cursor.fetchall()
            
            if specific_messages:
                print(f"Found {len(specific_messages)} messages:")
                for msg in specific_messages:
                    msg_id, role, content, timestamp = msg
                    content_preview = content[:80] + "..." if len(content) > 80 else content
                    print(f"  - {role}: {content_preview}")
            else:
                print(f"No messages found for conversation {test_conv_id}")

if __name__ == "__main__":
    debug_conversations()
