import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Meeting:
    """会議モデル"""
    
    def __init__(self, line_user_id: str, meeting_name: str, start_time: datetime, duration: int):
        self.line_user_id = line_user_id
        self.meeting_name = meeting_name
        self.start_time = start_time
        self.duration = duration
        self.meeting_id: Optional[str] = None
        self.meeting_password: Optional[str] = None
        self.meeting_url: Optional[str] = None
        self.google_event_id: Optional[str] = None
        self.created_at: Optional[datetime] = None
    
    def save(self) -> int:
        """会議情報をデータベースに保存"""
        try:
            conn = sqlite3.connect('meetings.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO meetings (
                    line_user_id, meeting_id, meeting_password, meeting_url,
                    meeting_name, start_time, duration, google_event_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.line_user_id, self.meeting_id, self.meeting_password,
                self.meeting_url, self.meeting_name, self.start_time,
                self.duration, self.google_event_id
            ))
            
            meeting_db_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"会議保存完了: ID {meeting_db_id}")
            return meeting_db_id
            
        except Exception as e:
            logger.error(f"会議保存エラー: {str(e)}")
            raise
    
    @classmethod
    def get_by_user_id(cls, line_user_id: str) -> List[Dict[str, Any]]:
        """ユーザーの会議一覧取得"""
        try:
            conn = sqlite3.connect('meetings.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM meetings 
                WHERE line_user_id = ? 
                ORDER BY start_time DESC
            ''', (line_user_id,))
            
            meetings = []
            for row in cursor.fetchall():
                meeting = {
                    'id': row[0],
                    'line_user_id': row[1],
                    'meeting_id': row[2],
                    'meeting_password': row[3],
                    'meeting_url': row[4],
                    'meeting_name': row[5],
                    'start_time': row[6],
                    'duration': row[7],
                    'created_at': row[8],
                    'google_event_id': row[9]
                }
                meetings.append(meeting)
            
            conn.close()
            return meetings
            
        except Exception as e:
            logger.error(f"会議取得エラー: {str(e)}")
            raise
    
    @classmethod
    def get_by_meeting_id(cls, meeting_id: str) -> Optional[Dict[str, Any]]:
        """会議IDで会議情報取得"""
        try:
            conn = sqlite3.connect('meetings.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM meetings WHERE meeting_id = ?
            ''', (meeting_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'line_user_id': row[1],
                    'meeting_id': row[2],
                    'meeting_password': row[3],
                    'meeting_url': row[4],
                    'meeting_name': row[5],
                    'start_time': row[6],
                    'duration': row[7],
                    'created_at': row[8],
                    'google_event_id': row[9]
                }
            return None
            
        except Exception as e:
            logger.error(f"会議取得エラー: {str(e)}")
            raise

