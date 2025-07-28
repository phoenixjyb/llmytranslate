#!/usr/bin/env python3
"""
Create sample conversation data for testing the history functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.services.database_manager import DatabaseManager
from src.services.user_auth_service import UserAuthService
from src.models.user_models import UserLogin
import uuid
from datetime import datetime, timedelta


async def create_sample_data():
    """Create sample users and conversations for testing."""
    
    print("🔄 Creating sample conversation data...")
    
    # Initialize services
    db_manager = DatabaseManager()
    auth_service = UserAuthService()
    
    # Check if demo users exist
    try:
        # Try to authenticate demo user
        demo_login = UserLogin(username_or_email="demo_user", password="Password123")
        user_result = await auth_service.authenticate_user(demo_login)
        if user_result:
            user_id = user_result.user_id
            print(f"✅ Found demo user: {user_id}")
            
            # Create sample conversations for demo user
            conversations = [
                {
                    "title": "Getting Started with AI",
                    "messages": [
                        {"role": "user", "content": "Hello! Can you help me understand how AI works?"},
                        {"role": "assistant", "content": "Hello! I'd be happy to help you understand AI. Artificial Intelligence refers to computer systems that can perform tasks that typically require human intelligence, such as learning, reasoning, and problem-solving. What specific aspect of AI would you like to explore?"},
                        {"role": "user", "content": "How does machine learning differ from traditional programming?"},
                        {"role": "assistant", "content": "Great question! In traditional programming, we write explicit instructions for the computer to follow. In machine learning, we provide data and let the algorithm learn patterns from that data to make predictions or decisions. Instead of programming rules, we train models to recognize patterns."}
                    ]
                },
                {
                    "title": "Translation Help",
                    "messages": [
                        {"role": "user", "content": "Can you translate 'Hello, how are you?' to Spanish?"},
                        {"role": "assistant", "content": "Sure! 'Hello, how are you?' in Spanish is 'Hola, ¿cómo estás?'"},
                        {"role": "user", "content": "What about French?"},
                        {"role": "assistant", "content": "In French, it would be 'Bonjour, comment allez-vous?' (formal) or 'Salut, comment ça va?' (informal)."}
                    ]
                },
                {
                    "title": "Programming Questions",
                    "messages": [
                        {"role": "user", "content": "What's the difference between Python and JavaScript?"},
                        {"role": "assistant", "content": "Python and JavaScript are both popular programming languages, but they have different strengths:\n\n**Python:**\n- General-purpose language\n- Great for data science, AI/ML, web backends\n- Clean, readable syntax\n- Interpreted language\n\n**JavaScript:**\n- Originally for web browsers\n- Now used for full-stack development (Node.js)\n- Dynamic and flexible\n- Event-driven programming\n\nBoth are excellent choices depending on your project needs!"}
                    ]
                }
            ]
            
            # Create conversations with messages
            for i, conv_data in enumerate(conversations):
                conversation_id = f"demo-conv-{i+1}-{int(datetime.now().timestamp())}"
                
                # Create conversation metadata
                success = db_manager.create_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=conv_data["title"],
                    platform="web"
                )
                
                if success:
                    print(f"✅ Created conversation: {conv_data['title']}")
                    
                    # Add messages to conversation
                    for j, message in enumerate(conv_data["messages"]):
                        message_id = f"{conversation_id}-msg-{j+1}"
                        message_success = db_manager.add_message(
                            conversation_id=conversation_id,
                            message_id=message_id,
                            role=message["role"],
                            content=message["content"],
                            model_used="gemma3:latest" if message["role"] == "assistant" else None,
                            processing_time_ms=150 if message["role"] == "assistant" else None
                        )
                        
                        if message_success:
                            print(f"  ✅ Added {message['role']} message")
                        else:
                            print(f"  ❌ Failed to add {message['role']} message")
                else:
                    print(f"❌ Failed to create conversation: {conv_data['title']}")
            
            print(f"\n🎉 Sample data creation complete!")
            print(f"📊 Demo user ({user_id}) now has {len(conversations)} sample conversations")
            print(f"🌐 Visit http://localhost:8000/auth.html to login as 'demo_user' with password 'Password123'")
            print(f"💬 Then visit http://localhost:8000/chat to test the conversation history feature")
            
        else:
            print("❌ Demo user not found or authentication failed. Please run the user initialization script first.")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
