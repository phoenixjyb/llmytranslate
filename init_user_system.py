"""
Initialize and test the user management system.
Sets up the database and creates demo users for testing.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.user_auth_service import user_auth_service
from src.services.database_manager import db_manager
from src.models.user_models import UserRegistration, UserLogin


async def initialize_user_system():
    """Initialize the user management system."""
    print("🚀 Initializing User Management System...")
    
    # Initialize database
    db_manager.init_database()
    print("✅ Database initialized")
    
    # Migrate existing conversations if needed
    db_manager.migrate_existing_conversations()
    print("✅ Conversation migration completed")
    
    # Create demo users for testing
    demo_users = [
        {
            "username": "demo_user",
            "email": "demo@example.com",
            "password": "Password123",
            "first_name": "Demo",
            "last_name": "User"
        },
        {
            "username": "admin_user",
            "email": "admin@example.com", 
            "password": "Admin123",
            "first_name": "Admin",
            "last_name": "User"
        }
    ]
    
    print("\n👥 Creating demo users...")
    for user_data in demo_users:
        try:
            registration = UserRegistration(**user_data)
            user_profile = await user_auth_service.register_user(registration)
            print(f"✅ Created user: {user_profile.username} ({user_profile.email})")
        except Exception as e:
            if "already exists" in str(e):
                print(f"ℹ️  User {user_data['username']} already exists")
            else:
                print(f"❌ Failed to create user {user_data['username']}: {e}")
    
    print("\n🧪 Testing authentication...")
    
    # Test login
    try:
        login_data = UserLogin(
            username_or_email="demo_user",
            password="Password123",
            remember_me=False
        )
        
        user_profile = await user_auth_service.authenticate_user(login_data)
        if user_profile:
            print(f"✅ Authentication test successful for {user_profile.username}")
            
            # Test session creation
            token_response = await user_auth_service.create_session(
                user_profile, "127.0.0.1", "Test User Agent"
            )
            print(f"✅ Session creation successful. Token type: {token_response.token_type}")
            
        else:
            print("❌ Authentication test failed")
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
    
    # Test guest session
    try:
        guest_session = await user_auth_service.create_guest_session(
            "127.0.0.1", "Test Guest Agent"
        )
        print(f"✅ Guest session created: {guest_session.session_id}")
        
    except Exception as e:
        print(f"❌ Guest session test error: {e}")
    
    print("\n✨ User management system initialization complete!")
    print("\n📋 Summary:")
    print("   • Database tables created")
    print("   • Demo users available:")
    print("     - Username: demo_user, Password: Password123")
    print("     - Username: admin_user, Password: Admin123")
    print("   • Guest access enabled")
    print("   • Authentication system ready")
    print("\n🌐 You can now:")
    print("   1. Access /auth.html for login/registration")
    print("   2. Use guest access without registration")
    print("   3. Access /chat.html for authenticated chat")


async def test_user_flows():
    """Test complete user flows."""
    print("\n🔍 Testing user flows...")
    
    # Test registration flow
    try:
        new_user = UserRegistration(
            username="test_user_" + str(asyncio.get_event_loop().time())[-4:],
            email=f"test_{str(asyncio.get_event_loop().time())[-4:]}@example.com",
            password="TestPass123",
            first_name="Test",
            last_name="User"
        )
        
        user_profile = await user_auth_service.register_user(new_user)
        print(f"✅ Registration flow: Created {user_profile.username}")
        
        # Test immediate login after registration
        login_data = UserLogin(
            username_or_email=new_user.username,
            password=new_user.password,
            remember_me=True
        )
        
        authenticated_user = await user_auth_service.authenticate_user(login_data)
        if authenticated_user:
            print("✅ Login after registration: Success")
        else:
            print("❌ Login after registration: Failed")
            
    except Exception as e:
        print(f"❌ Registration flow error: {e}")
    
    print("✅ User flow testing complete")


if __name__ == "__main__":
    asyncio.run(initialize_user_system())
    asyncio.run(test_user_flows())
