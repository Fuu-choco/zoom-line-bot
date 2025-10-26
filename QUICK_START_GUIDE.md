# クイックスタートガイド

## 概要
このガイドでは、Zoom API + Google Calendar + LINE Bot 会議管理システムを最短時間で構築する手順を説明します。

## 前提条件
- Python 3.8+ がインストールされている
- GitHub アカウント
- LINE アカウント
- Zoom アカウント
- Google アカウント

## 1. プロジェクト初期化（5分）

### 1.1 ディレクトリ作成
```bash
mkdir zoom-meeting-bot
cd zoom-meeting-bot
```

### 1.2 仮想環境作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 1.3 依存関係インストール
```bash
pip install Flask line-bot-sdk requests google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client PyJWT python-dotenv
```

## 2. 基本ファイル作成（10分）

### 2.1 requirements.txt
```txt
Flask==2.3.3
line-bot-sdk==3.5.0
requests==2.31.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
PyJWT==2.8.0
python-dotenv==1.0.0
```

### 2.2 .env ファイル
```bash
# LINE Bot
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Zoom API
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret

# Google Calendar
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

### 2.3 プロジェクト構造
```
zoom-meeting-bot/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── database/
│   ├── __init__.py
│   ├── models.py
│   └── init_db.py
├── services/
│   ├── __init__.py
│   ├── line_bot.py
│   ├── zoom_api.py
│   └── google_calendar.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

## 3. データベース実装（5分）

### 3.1 database/init_db.py
```python
import sqlite3
import os

def init_database():
    conn = sqlite3.connect('meetings.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    print("データベース初期化完了")

if __name__ == "__main__":
    init_database()
```

### 3.2 データベース初期化
```bash
python database/init_db.py
```

## 4. 設定管理（5分）

### 4.1 config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
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
```

## 5. メインアプリケーション（15分）

### 5.1 app.py
```python
from flask import Flask, request, jsonify
from config import Config
import logging

app = Flask(__name__)
app.config.from_object(Config)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    return {"status": "healthy"}

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # LINE Bot のWebhook処理
        from services.line_bot import handle_webhook
        return handle_webhook(request)
    except Exception as e:
        logger.error(f"Webhook エラー: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    # データベース初期化
    from database.init_db import init_database
    init_database()
    
    app.run(host='0.0.0.0', port=8000, debug=True)
```

## 6. LINE Bot 実装（20分）

### 6.1 services/line_bot.py
```python
from flask import request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from config import Config
import logging

logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

def handle_webhook(request):
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({"error": "Invalid signature"}), 400
    
    return jsonify({"status": "OK"})

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    
    logger.info(f"メッセージ受信: {message_text} from {user_id}")
    
    if message_text == "会議作成":
        reply_text = "会議名を教えてください"
    else:
        reply_text = "「会議作成」と入力してください"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
```

## 7. Zoom API 実装（15分）

### 7.1 services/zoom_api.py
```python
import jwt
import requests
import time
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_zoom_token():
    """Zoom JWT トークン生成"""
    payload = {
        "iss": Config.ZOOM_API_KEY,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, Config.ZOOM_API_SECRET, algorithm="HS256")
    return token

def create_meeting(meeting_data):
    """Zoom 会議作成"""
    try:
        token = get_zoom_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://api.zoom.us/v2/users/me/meetings'
        
        response = requests.post(url, headers=headers, json=meeting_data)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logger.error(f"Zoom API エラー: {str(e)}")
        raise
```

## 8. Google Calendar 実装（15分）

### 8.1 services/google_calendar.py
```python
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_google_service():
    """Google Calendar サービス取得"""
    try:
        credentials_info = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Google Calendar 認証エラー: {str(e)}")
        raise

def create_calendar_event(event_data):
    """Google Calendar イベント作成"""
    try:
        service = get_google_service()
        event = service.events().insert(calendarId='primary', body=event_data).execute()
        return event
    except Exception as e:
        logger.error(f"Google Calendar イベント作成エラー: {str(e)}")
        raise
```

## 9. ローカルテスト（10分）

### 9.1 アプリケーション起動
```bash
python app.py
```

### 9.2 ngrok でWebhook設定
```bash
# ngrok インストール（未インストールの場合）
# https://ngrok.com/download

# ngrok 起動
ngrok http 8000
```

### 9.3 LINE Bot Webhook設定
1. LINE Developers Console でWebhook URL設定
2. URL: `https://your-ngrok-url.ngrok.io/webhook`
3. 「Verify」で検証

## 10. Railway デプロイ（15分）

### 10.1 Railway CLI インストール
```bash
npm install -g @railway/cli
```

### 10.2 Railway ログイン・初期化
```bash
railway login
railway init
```

### 10.3 環境変数設定
```bash
railway variables set LINE_CHANNEL_ACCESS_TOKEN=your_token
railway variables set LINE_CHANNEL_SECRET=your_secret
railway variables set ZOOM_API_KEY=your_zoom_key
railway variables set ZOOM_API_SECRET=your_zoom_secret
railway variables set GOOGLE_CREDENTIALS_JSON=your_google_credentials
```

### 10.4 デプロイ実行
```bash
railway up
```

## 11. 動作確認（5分）

### 11.1 ヘルスチェック
```bash
curl https://your-app.railway.app/health
```

### 11.2 LINE Bot テスト
1. LINE アプリでBotを友達追加
2. 「会議作成」と送信
3. 対話フローが動作するか確認

## 12. 次のステップ

基本的な実装が完了したら、以下を実装してください：

1. **完全な対話フロー実装**
2. **エラーハンドリング強化**
3. **データベース連携**
4. **ログ機能強化**
5. **テスト実装**

詳細な実装手順は `IMPLEMENTATION_PLAN.md` を参照してください。

## トラブルシューティング

### よくあるエラー
1. **認証エラー**: 環境変数が正しく設定されているか確認
2. **Webhook エラー**: URLが正しく設定されているか確認
3. **データベースエラー**: ファイル権限を確認

### ログ確認
```bash
# ローカル
python app.py

# Railway
railway logs --follow
```

## 参考資料

- [README.md](README.md) - システム概要
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 詳細実装計画
- [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) - API認証情報取得手順
- [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) - Railway デプロイ手順

