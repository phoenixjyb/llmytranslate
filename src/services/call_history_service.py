"""
Call History Service for Phone Call Mode
Manages call history, statistics, and session records
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class CallHistoryService:
    """Service to manage phone call history and statistics"""
    
    def __init__(self, db_path: str = "data/call_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
        logger.info(f"Call history service initialized with database: {db_path}")
    
    def init_database(self):
        """Initialize the call history database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    kid_friendly_mode BOOLEAN DEFAULT FALSE,
                    language TEXT DEFAULT 'english',
                    interrupted_count INTEGER DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Call messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_messages (
                    id TEXT PRIMARY KEY,
                    call_id TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER DEFAULT 0,
                    was_interrupted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (call_id) REFERENCES calls (id)
                )
            """)
            
            # Call statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_stats (
                    user_id TEXT PRIMARY KEY,
                    total_calls INTEGER DEFAULT 0,
                    total_duration_seconds INTEGER DEFAULT 0,
                    average_call_duration REAL DEFAULT 0.0,
                    total_messages INTEGER DEFAULT 0,
                    kid_friendly_calls INTEGER DEFAULT 0,
                    last_call_time TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_user_id ON calls (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_session_id ON calls (session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_start_time ON calls (start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_call_id ON call_messages (call_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON call_messages (timestamp)")
            
            conn.commit()
            logger.info("Call history database initialized successfully")
    
    def start_call(self, user_id: str, session_id: str, kid_friendly_mode: bool = False, 
                   language: str = 'english') -> str:
        """Start a new call record"""
        call_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO calls (id, user_id, session_id, start_time, status, 
                                 kid_friendly_mode, language, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """, (call_id, user_id, session_id, now, kid_friendly_mode, language, now, now))
            conn.commit()
        
        logger.info(f"Call started: {call_id} for user {user_id}")
        return call_id
    
    def end_call(self, call_id: str) -> bool:
        """End a call record"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get call start time
            cursor.execute("SELECT start_time FROM calls WHERE id = ?", (call_id,))
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Call not found: {call_id}")
                return False
            
            start_time = datetime.fromisoformat(result[0])
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            # Update call record
            cursor.execute("""
                UPDATE calls 
                SET end_time = ?, duration_seconds = ?, status = 'completed', updated_at = ?
                WHERE id = ?
            """, (now, duration, now, call_id))
            
            # Update user statistics
            self._update_user_stats(cursor, call_id)
            
            conn.commit()
        
        logger.info(f"Call ended: {call_id}, duration: {duration} seconds")
        return True
    
    def add_message(self, call_id: str, speaker: str, message: str, 
                   duration_ms: int = 0, was_interrupted: bool = False) -> str:
        """Add a message to a call"""
        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add message
            cursor.execute("""
                INSERT INTO call_messages (id, call_id, speaker, message, timestamp, 
                                         duration_ms, was_interrupted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message_id, call_id, speaker, message, now, duration_ms, was_interrupted))
            
            # Update call message count
            cursor.execute("""
                UPDATE calls 
                SET message_count = message_count + 1, updated_at = ?
                WHERE id = ?
            """, (now, call_id))
            
            # Update interrupt count if message was interrupted
            if was_interrupted:
                cursor.execute("""
                    UPDATE calls 
                    SET interrupted_count = interrupted_count + 1
                    WHERE id = ?
                """, (call_id,))
            
            conn.commit()
        
        logger.info(f"Message added to call {call_id}: {speaker} - {len(message)} chars")
        return message_id
    
    def get_call_history(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get call history for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, start_time, end_time, duration_seconds, status,
                       kid_friendly_mode, language, interrupted_count, message_count
                FROM calls 
                WHERE user_id = ?
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            
            rows = cursor.fetchall()
            
            calls = []
            for row in rows:
                call = {
                    'id': row[0],
                    'session_id': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'duration_seconds': row[4],
                    'status': row[5],
                    'kid_friendly_mode': bool(row[6]),
                    'language': row[7],
                    'interrupted_count': row[8],
                    'message_count': row[9]
                }
                calls.append(call)
        
        return calls
    
    def get_call_details(self, call_id: str) -> Optional[Dict]:
        """Get detailed information about a specific call"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get call info
            cursor.execute("""
                SELECT id, user_id, session_id, start_time, end_time, duration_seconds,
                       status, kid_friendly_mode, language, interrupted_count, message_count
                FROM calls WHERE id = ?
            """, (call_id,))
            
            call_row = cursor.fetchone()
            if not call_row:
                return None
            
            # Get messages
            cursor.execute("""
                SELECT speaker, message, timestamp, duration_ms, was_interrupted
                FROM call_messages 
                WHERE call_id = ?
                ORDER BY timestamp ASC
            """, (call_id,))
            
            message_rows = cursor.fetchall()
            
            call_details = {
                'id': call_row[0],
                'user_id': call_row[1],
                'session_id': call_row[2],
                'start_time': call_row[3],
                'end_time': call_row[4],
                'duration_seconds': call_row[5],
                'status': call_row[6],
                'kid_friendly_mode': bool(call_row[7]),
                'language': call_row[8],
                'interrupted_count': call_row[9],
                'message_count': call_row[10],
                'messages': []
            }
            
            for msg_row in message_rows:
                message = {
                    'speaker': msg_row[0],
                    'message': msg_row[1],
                    'timestamp': msg_row[2],
                    'duration_ms': msg_row[3],
                    'was_interrupted': bool(msg_row[4])
                }
                call_details['messages'].append(message)
        
        return call_details
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get statistics for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT total_calls, total_duration_seconds, average_call_duration,
                       total_messages, kid_friendly_calls, last_call_time
                FROM call_stats WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return {
                    'total_calls': 0,
                    'total_duration_seconds': 0,
                    'average_call_duration': 0.0,
                    'total_messages': 0,
                    'kid_friendly_calls': 0,
                    'last_call_time': None
                }
            
            return {
                'total_calls': row[0],
                'total_duration_seconds': row[1],
                'average_call_duration': row[2],
                'total_messages': row[3],
                'kid_friendly_calls': row[4],
                'last_call_time': row[5]
            }
    
    def search_calls(self, user_id: str, search_term: str, limit: int = 10) -> List[Dict]:
        """Search calls by message content"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.id, c.session_id, c.start_time, c.end_time, 
                       c.duration_seconds, c.status, c.kid_friendly_mode, c.language
                FROM calls c
                JOIN call_messages m ON c.id = m.call_id
                WHERE c.user_id = ? AND m.message LIKE ?
                ORDER BY c.start_time DESC
                LIMIT ?
            """, (user_id, f'%{search_term}%', limit))
            
            rows = cursor.fetchall()
            
            calls = []
            for row in rows:
                call = {
                    'id': row[0],
                    'session_id': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'duration_seconds': row[4],
                    'status': row[5],
                    'kid_friendly_mode': bool(row[6]),
                    'language': row[7]
                }
                calls.append(call)
        
        return calls
    
    def _update_user_stats(self, cursor, call_id: str):
        """Update user statistics after a call ends"""
        # Get call details
        cursor.execute("""
            SELECT user_id, duration_seconds, kid_friendly_mode, message_count, start_time
            FROM calls WHERE id = ?
        """, (call_id,))
        
        result = cursor.fetchone()
        if not result:
            return
        
        user_id, duration, kid_friendly, msg_count, start_time = result
        
        # Get current stats or create new
        cursor.execute("SELECT * FROM call_stats WHERE user_id = ?", (user_id,))
        stats_row = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if stats_row:
            # Update existing stats
            new_total_calls = stats_row[1] + 1
            new_total_duration = stats_row[2] + duration
            new_average_duration = new_total_duration / new_total_calls
            new_total_messages = stats_row[4] + msg_count
            new_kid_friendly_calls = stats_row[5] + (1 if kid_friendly else 0)
            
            cursor.execute("""
                UPDATE call_stats 
                SET total_calls = ?, total_duration_seconds = ?, average_call_duration = ?,
                    total_messages = ?, kid_friendly_calls = ?, last_call_time = ?, updated_at = ?
                WHERE user_id = ?
            """, (new_total_calls, new_total_duration, new_average_duration,
                  new_total_messages, new_kid_friendly_calls, start_time, now, user_id))
        else:
            # Create new stats
            cursor.execute("""
                INSERT INTO call_stats (user_id, total_calls, total_duration_seconds,
                                      average_call_duration, total_messages, kid_friendly_calls,
                                      last_call_time, created_at, updated_at)
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, duration, float(duration), msg_count, 
                  1 if kid_friendly else 0, start_time, now, now))
    
    def cleanup_old_calls(self, days_to_keep: int = 90) -> int:
        """Clean up old call records"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get call IDs to delete
            cursor.execute("SELECT id FROM calls WHERE start_time < ?", (cutoff_date,))
            call_ids = [row[0] for row in cursor.fetchall()]
            
            if call_ids:
                # Delete messages first
                placeholders = ','.join(['?'] * len(call_ids))
                cursor.execute(f"DELETE FROM call_messages WHERE call_id IN ({placeholders})", call_ids)
                
                # Delete calls
                cursor.execute(f"DELETE FROM calls WHERE id IN ({placeholders})", call_ids)
                
                conn.commit()
                logger.info(f"Cleaned up {len(call_ids)} old calls")
            
            return len(call_ids)

# Global instance
call_history_service = CallHistoryService()
