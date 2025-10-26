import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class Config:
    """アプリケーション設定"""
    
    # LINE Bot
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    
    # Zoom API
    ZOOM_API_KEY = os.getenv('ZOOM_API_KEY')
    ZOOM_API_SECRET = os.getenv('ZOOM_API_SECRET')
    
    # Google Calendar
    GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
    
    # データベース
    DATABASE_URL = 'meetings.db'
    
    # アプリケーション設定
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    
    @classmethod
    def validate_config(cls):
        """設定値の検証"""
        required_vars = [
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET',
            'ZOOM_API_KEY',
            'ZOOM_API_SECRET',
            'GOOGLE_CREDENTIALS_JSON'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        
        return True

