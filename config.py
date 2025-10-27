import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class Config:
    """アプリケーション設定"""
    
    # LINE Bot
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
    
    # デバッグ用：環境変数の直接確認
    if not LINE_CHANNEL_SECRET:
        print("⚠️ LINE_CHANNEL_SECRETが見つかりません。環境変数を確認してください。")
        print(f"利用可能な環境変数: {list(os.environ.keys())}")
        # 代替の環境変数名を試す
        LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET') or os.getenv('line_channel_secret') or os.getenv('Line_Channel_Secret')
    
    # Zoom API
    ZOOM_API_KEY = os.getenv('ZOOM_API_KEY')  # Client ID
    ZOOM_API_SECRET = os.getenv('ZOOM_API_SECRET')  # Client Secret
    ZOOM_ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')  # Account ID
    
    # Google Calendar
    GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
    
    # データベース
    DATABASE_URL = 'meetings.db'
    
    # アプリケーション設定
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', os.getenv('RAILWAY_PORT', 8000)))
    
    # Railway環境検出
    IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    @classmethod
    def validate_config(cls):
        """設定値の検証"""
        required_vars = [
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET'
        ]
        
        optional_vars = [
            'ZOOM_API_KEY',
            'ZOOM_API_SECRET',
            'ZOOM_ACCOUNT_ID',
            'GOOGLE_CREDENTIALS_JSON'
        ]
        
        # デバッグ情報を出力
        print("=== 環境変数デバッグ情報 ===")
        for var in required_vars + optional_vars:
            value = getattr(cls, var)
            if value:
                # 機密情報は一部のみ表示
                if 'SECRET' in var or 'TOKEN' in var or 'KEY' in var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"{var}: {display_value}")
            else:
                print(f"{var}: 未設定")
        
        # 環境変数の直接確認
        print("\n=== 直接環境変数確認 ===")
        for var in required_vars:
            env_value = os.getenv(var)
            print(f"os.getenv('{var}'): {env_value[:8] + '...' if env_value and len(env_value) > 8 else env_value}")
        
        print("========================\n")
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        
        # オプション変数の確認
        missing_optional = []
        for var in optional_vars:
            if not getattr(cls, var):
                missing_optional.append(var)
        
        if missing_optional:
            print(f"警告: 以下のオプション環境変数が設定されていません: {', '.join(missing_optional)}")
            print("Zoom APIとGoogle Calendar APIの機能は無効になります")
        
        return True

