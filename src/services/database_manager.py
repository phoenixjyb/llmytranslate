"""
Database initialization and management utilities.
Sets up user tables and conversation management with user association.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for users and conversations."""
    
    def __init__(self, db_path: str = "data/llmytranslate.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables."""
        with sqlite3.connect(self.db_path) as conn:
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
            
            # Update conversation_metadata table to include user association
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    model_used TEXT DEFAULT 'gemma3:latest',
                    platform TEXT DEFAULT 'unknown',
                    is_guest_conversation BOOLEAN DEFAULT FALSE,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Conversation messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    model_used TEXT,
                    processing_time_ms INTEGER,
                    tokens_used INTEGER,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversation_metadata (conversation_id)
                )
            """)
            
            # API usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_time_ms INTEGER,
                    status_code INTEGER,
                    tokens_used INTEGER,
                    model_used TEXT,
                    is_guest BOOLEAN DEFAULT FALSE,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversation_metadata (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversation_metadata (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON conversation_messages (conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage (timestamp)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def migrate_existing_conversations(self):
        """Migrate existing conversations to include user association."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if we need to add user_id column to existing table
            cursor.execute("PRAGMA table_info(conversation_metadata)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("Migrating conversation_metadata table to include user association")
                
                # Add new columns
                cursor.execute("ALTER TABLE conversation_metadata ADD COLUMN user_id TEXT")
                cursor.execute("ALTER TABLE conversation_metadata ADD COLUMN session_id TEXT")
                cursor.execute("ALTER TABLE conversation_metadata ADD COLUMN is_guest_conversation BOOLEAN DEFAULT TRUE")
                
                # Mark all existing conversations as guest conversations
                cursor.execute("UPDATE conversation_metadata SET is_guest_conversation = TRUE WHERE user_id IS NULL")
                
                conn.commit()
                logger.info("Conversation migration completed")
    
    def create_conversation(self, conversation_id: str, user_id: Optional[str] = None, 
                          session_id: Optional[str] = None, title: Optional[str] = None,
                          model: str = "gemma3:latest", platform: str = "unknown") -> bool:
        """Create a new conversation with user association."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                is_guest = user_id is None
                
                cursor.execute("""
                    INSERT INTO conversation_metadata (
                        conversation_id, user_id, session_id, title, model_used, 
                        platform, is_guest_conversation, created_at, last_message_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id, user_id, session_id, title, model, 
                    platform, is_guest, datetime.utcnow(), datetime.utcnow()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False
    
    def add_message(self, conversation_id: str, message_id: str, role: str, 
                   content: str, model_used: str = None, processing_time_ms: int = None,
                   tokens_used: int = None) -> bool:
        """Add a message to a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert message
                cursor.execute("""
                    INSERT INTO conversation_messages (
                        conversation_id, message_id, role, content, model_used,
                        processing_time_ms, tokens_used, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id, message_id, role, content, model_used,
                    processing_time_ms, tokens_used, datetime.utcnow()
                ))
                
                # Update conversation metadata
                cursor.execute("""
                    UPDATE conversation_metadata 
                    SET message_count = message_count + 1, last_message_at = ?
                    WHERE conversation_id = ?
                """, (datetime.utcnow(), conversation_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> list:
        """Get conversations for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT conversation_id, title, created_at, last_message_at,
                           message_count, model_used, platform
                    FROM conversation_metadata
                    WHERE user_id = ? AND is_guest_conversation = FALSE
                    ORDER BY last_message_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'conversation_id': row[0],
                        'title': row[1] or f"Chat {row[0][:8]}",
                        'created_at': row[2],
                        'last_message_at': row[3],
                        'message_count': row[4],
                        'model_used': row[5],
                        'platform': row[6]
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []
    
    def get_guest_conversations(self, session_id: str) -> list:
        """Get conversations for a guest session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT conversation_id, title, created_at, last_message_at,
                           message_count, model_used, platform
                    FROM conversation_metadata
                    WHERE session_id = ? AND is_guest_conversation = TRUE
                    ORDER BY last_message_at DESC
                    LIMIT 10
                """, (session_id,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'conversation_id': row[0],
                        'title': row[1] or f"Guest Chat {row[0][:8]}",
                        'created_at': row[2],
                        'last_message_at': row[3],
                        'message_count': row[4],
                        'model_used': row[5],
                        'platform': row[6]
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to get guest conversations: {e}")
            return []
    
    def cleanup_old_guest_conversations(self, days: int = 7):
        """Clean up old guest conversations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.utcnow().replace(microsecond=0) - timedelta(days=days)
                
                # Get conversation IDs to delete
                cursor.execute("""
                    SELECT conversation_id FROM conversation_metadata
                    WHERE is_guest_conversation = TRUE AND last_message_at < ?
                """, (cutoff_date,))
                
                conversation_ids = [row[0] for row in cursor.fetchall()]
                
                if conversation_ids:
                    # Delete messages first
                    cursor.executemany(
                        "DELETE FROM conversation_messages WHERE conversation_id = ?",
                        [(cid,) for cid in conversation_ids]
                    )
                    
                    # Delete conversation metadata
                    cursor.executemany(
                        "DELETE FROM conversation_metadata WHERE conversation_id = ?",
                        [(cid,) for cid in conversation_ids]
                    )
                    
                    conn.commit()
                    logger.info(f"Cleaned up {len(conversation_ids)} old guest conversations")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
    
    def get_conversation_messages(self, conversation_id: str) -> list:
        """Get all messages for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT message_id, role, content, timestamp, model_used,
                           processing_time_ms, tokens_used
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'message_id': row[0],
                        'role': row[1],
                        'content': row[2],
                        'timestamp': row[3],
                        'model_used': row[4],
                        'processing_time_ms': row[5],
                        'tokens_used': row[6]
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            return []

    def log_api_usage(self, user_id: Optional[str], session_id: Optional[str],
                     endpoint: str, method: str, status_code: int,
                     processing_time_ms: int = None, tokens_used: int = None,
                     model_used: str = None, is_guest: bool = False,
                     ip_address: str = None, user_agent: str = None):
        """Log API usage for analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO api_usage (
                        user_id, session_id, endpoint, method, status_code,
                        processing_time_ms, tokens_used, model_used, is_guest,
                        ip_address, user_agent, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, session_id, endpoint, method, status_code,
                    processing_time_ms, tokens_used, model_used, is_guest,
                    ip_address, user_agent, datetime.utcnow()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")


# Global database manager instance
db_manager = DatabaseManager()
