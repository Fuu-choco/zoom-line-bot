import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def init_database():
    """データベース初期化"""
    try:
        conn = sqlite3.connect('meetings.db')
        cursor = conn.cursor()
        
        # meetings テーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_user_id TEXT NOT NULL,
                meeting_id TEXT NOT NULL,
                meeting_password TEXT,
                meeting_url TEXT,
                meeting_name TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                duration INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                google_event_id TEXT
            )
        ''')
        
        # インデックス作成
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_line_user_id 
            ON meetings(line_user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_start_time 
            ON meetings(start_time)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("データベース初期化完了")
        print("✅ データベース初期化完了")
        
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        print(f"❌ データベース初期化エラー: {str(e)}")
        raise

def get_connection():
    """データベース接続取得"""
    return sqlite3.connect('meetings.db')

if __name__ == "__main__":
    init_database()

