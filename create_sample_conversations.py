#!/usr/bin/env python3
"""
Create sample conversation data for testing the history functionality.
This script creates some demo conversations for the demo_user account.
"""

import sys
import os
from datetime import datetime, timedelta
import uuid

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.database_manager import DatabaseManager

def create_sample_conversations():
    """Create sample conversations for testing."""
    
    db_manager = DatabaseManager()
    
    # Sample conversations for demo_user
    demo_user_id = "demo_user"
    
    conversations = [
        {
            "title": "Python Programming Help",
            "messages": [
                {"role": "user", "content": "Can you help me understand Python list comprehensions?"},
                {"role": "assistant", "content": "Of course! List comprehensions are a concise way to create lists in Python. They follow the pattern: [expression for item in iterable if condition]. For example: [x**2 for x in range(10) if x % 2 == 0] creates a list of squares of even numbers from 0 to 8."},
                {"role": "user", "content": "That's helpful! Can you show me a more complex example?"},
                {"role": "assistant", "content": "Sure! Here's a more complex example: [[i*j for j in range(1, 4)] for i in range(1, 4)] creates a nested list representing a multiplication table. This results in [[1, 2, 3], [2, 4, 6], [3, 6, 9]]."}
            ]
        },
        {
            "title": "Travel Planning Discussion",
            "messages": [
                {"role": "user", "content": "I'm planning a trip to Japan. What are some must-visit places?"},
                {"role": "assistant", "content": "Japan has amazing destinations! For first-time visitors, I'd recommend: Tokyo (modern culture, shopping, food), Kyoto (traditional temples, geishas), Osaka (street food, Osaka Castle), Mount Fuji area (scenic beauty), and Hiroshima (historical significance, Peace Memorial). Each offers unique experiences!"},
                {"role": "user", "content": "How many days would you recommend for this itinerary?"},
                {"role": "assistant", "content": "I'd recommend at least 10-14 days for a comprehensive trip covering these locations. Here's a suggested breakdown: Tokyo (4-5 days), Kyoto (3-4 days), Osaka (2-3 days), Mount Fuji area (1-2 days), and Hiroshima (1-2 days). This allows time to explore each destination without rushing."}
            ]
        },
        {
            "title": "Recipe Recommendations",
            "messages": [
                {"role": "user", "content": "I need a quick and healthy dinner recipe for tonight."},
                {"role": "assistant", "content": "Here's a quick and healthy recipe: **Lemon Garlic Salmon with Vegetables**\n\nIngredients:\n- 2 salmon fillets\n- 1 zucchini, sliced\n- 1 bell pepper, chopped\n- 2 tbsp olive oil\n- 2 cloves garlic, minced\n- 1 lemon (juice and zest)\n- Salt, pepper, herbs\n\nInstructions:\n1. Preheat oven to 400°F\n2. Place salmon and vegetables on a baking sheet\n3. Drizzle with olive oil, lemon juice, garlic, and seasonings\n4. Bake for 15-20 minutes\n\nReady in 25 minutes and packed with protein and nutrients!"}
            ]
        }
    ]
    
    print("Creating sample conversations...")
    
    for i, conv_data in enumerate(conversations):
        # Create conversation ID
        conversation_id = f"demo-{uuid.uuid4().hex[:8]}"
        created_time = datetime.utcnow() - timedelta(days=i+1)
        
        # Create conversation metadata
        success = db_manager.create_conversation(
            conversation_id=conversation_id,
            user_id=demo_user_id,
            session_id=None,
            title=conv_data["title"],
            model_used="gemma3:latest",
            platform="web",
            is_guest_conversation=False
        )
        
        if success:
            print(f"✓ Created conversation: {conv_data['title']}")
            
            # Add messages
            for j, message in enumerate(conv_data["messages"]):
                message_id = f"msg-{uuid.uuid4().hex[:8]}"
                db_manager.add_message(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    role=message["role"],
                    content=message["content"],
                    model_used="gemma3:latest" if message["role"] == "assistant" else None,
                    processing_time_ms=150 if message["role"] == "assistant" else None,
                    tokens_used=len(message["content"].split()) * 1.3 if message["role"] == "assistant" else None
                )
            
            print(f"  └─ Added {len(conv_data['messages'])} messages")
        else:
            print(f"✗ Failed to create conversation: {conv_data['title']}")
    
    print("\nSample conversations created successfully!")
    print("You can now test the conversation history feature by:")
    print("1. Logging in with demo_user / Password123")
    print("2. Clicking the 'History' button in the chat interface")
    print("3. Selecting a conversation to load its history")

if __name__ == "__main__":
    create_sample_conversations()
